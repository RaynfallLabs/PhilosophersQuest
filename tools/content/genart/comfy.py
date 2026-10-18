"""The two drawing passes, sent to the ComfyUI running on this machine.

Pass 1 (FLUX.2 klein 4B) decides WHAT is drawn: it follows a written brief closely
(pose, empty or full hands, one figure, a flat key-colour background).
Pass 2 (the SDXL pixel-art model, image-to-image) decides HOW it is drawn: it
keeps pass 1's picture and redraws it as crisp pixel art.
"""
import json, os, shutil, time, urllib.error, urllib.parse, urllib.request

HOST = 'http://127.0.0.1:8188'
COMFY_INPUT = r'C:\Users\brand\Documents\ComfyUI_windows_portable\ComfyUI\input'
KLEIN = 'flux-2-klein-base-4b-fp8.safetensors'
PIXEL = 'pixelArtDiffusionXL_spriteShaper.safetensors'


def _post(path, data):
    req = urllib.request.Request(HOST + path, json.dumps(data).encode(), {'Content-Type': 'application/json'})
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        raise RuntimeError('ComfyUI refused the workflow: ' + e.read().decode()[:1500])


def _get(path):
    return json.load(urllib.request.urlopen(HOST + path))


def running():
    try:
        _get('/system_stats')
        return True
    except Exception:
        return False


def draft_workflow(prompt, negative, seed, size=1024, steps=20, cfg=5.0):
    return {
        'm': {'class_type': 'UNETLoader', 'inputs': {'unet_name': KLEIN, 'weight_dtype': 'default'}},
        'c': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': 'qwen_3_4b.safetensors', 'type': 'flux2', 'device': 'default'}},
        'v': {'class_type': 'VAELoader', 'inputs': {'vae_name': 'flux2-vae.safetensors'}},
        'p': {'class_type': 'CLIPTextEncode', 'inputs': {'text': prompt, 'clip': ['c', 0]}},
        'n': {'class_type': 'CLIPTextEncode', 'inputs': {'text': negative, 'clip': ['c', 0]}},
        'l': {'class_type': 'EmptyFlux2LatentImage', 'inputs': {'width': size, 'height': size, 'batch_size': 1}},
        's': {'class_type': 'KSamplerSelect', 'inputs': {'sampler_name': 'euler'}},
        'sg': {'class_type': 'Flux2Scheduler', 'inputs': {'steps': steps, 'width': size, 'height': size}},
        'r': {'class_type': 'RandomNoise', 'inputs': {'noise_seed': seed}},
        'g': {'class_type': 'CFGGuider', 'inputs': {'cfg': cfg, 'model': ['m', 0], 'positive': ['p', 0], 'negative': ['n', 0]}},
        'k': {'class_type': 'SamplerCustomAdvanced',
              'inputs': {'noise': ['r', 0], 'guider': ['g', 0], 'sampler': ['s', 0], 'sigmas': ['sg', 0], 'latent_image': ['l', 0]}},
        'd': {'class_type': 'VAEDecode', 'inputs': {'samples': ['k', 0], 'vae': ['v', 0]}},
        'o': {'class_type': 'SaveImage', 'inputs': {'filename_prefix': 'genart_draft', 'images': ['d', 0]}},
    }


def edit_workflow(input_names, prompt, negative, seed, size=1024, steps=20, cfg=5.0):
    """klein redraws the first picture as the prompt says, seeing every picture in
    `input_names` as a reference (the first is the one being edited; any others are
    things it may copy from). Everything the prompt does not change stays close."""
    wf = {
        'm': {'class_type': 'UNETLoader', 'inputs': {'unet_name': KLEIN, 'weight_dtype': 'default'}},
        'c': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': 'qwen_3_4b.safetensors', 'type': 'flux2', 'device': 'default'}},
        'v': {'class_type': 'VAELoader', 'inputs': {'vae_name': 'flux2-vae.safetensors'}},
        'p': {'class_type': 'CLIPTextEncode', 'inputs': {'text': prompt, 'clip': ['c', 0]}},
        'n': {'class_type': 'CLIPTextEncode', 'inputs': {'text': negative, 'clip': ['c', 0]}},
        'l': {'class_type': 'EmptyFlux2LatentImage', 'inputs': {'width': size, 'height': size, 'batch_size': 1}},
        's': {'class_type': 'KSamplerSelect', 'inputs': {'sampler_name': 'euler'}},
        'sg': {'class_type': 'Flux2Scheduler', 'inputs': {'steps': steps, 'width': size, 'height': size}},
        'r': {'class_type': 'RandomNoise', 'inputs': {'noise_seed': seed}},
        'd': {'class_type': 'VAEDecode', 'inputs': {'samples': ['k', 0], 'vae': ['v', 0]}},
        'o': {'class_type': 'SaveImage', 'inputs': {'filename_prefix': 'genart_edit', 'images': ['d', 0]}},
    }
    pos, neg = ['p', 0], ['n', 0]
    for j, name in enumerate(input_names):
        wf[f'i{j}'] = {'class_type': 'LoadImage', 'inputs': {'image': name}}
        wf[f'e{j}'] = {'class_type': 'VAEEncode', 'inputs': {'pixels': [f'i{j}', 0], 'vae': ['v', 0]}}
        wf[f'rp{j}'] = {'class_type': 'ReferenceLatent', 'inputs': {'conditioning': pos, 'latent': [f'e{j}', 0]}}
        wf[f'rn{j}'] = {'class_type': 'ReferenceLatent', 'inputs': {'conditioning': neg, 'latent': [f'e{j}', 0]}}
        pos, neg = [f'rp{j}', 0], [f'rn{j}', 0]
    wf['g'] = {'class_type': 'CFGGuider', 'inputs': {'cfg': cfg, 'model': ['m', 0], 'positive': pos, 'negative': neg}}
    wf['k'] = {'class_type': 'SamplerCustomAdvanced',
               'inputs': {'noise': ['r', 0], 'guider': ['g', 0], 'sampler': ['s', 0], 'sigmas': ['sg', 0], 'latent_image': ['l', 0]}}
    return wf


def pixel_workflow(input_name, prompt, negative, seed, denoise=0.55):
    return {
        '2': {'class_type': 'CheckpointLoaderSimple', 'inputs': {'ckpt_name': PIXEL}},
        'i': {'class_type': 'LoadImage', 'inputs': {'image': input_name}},
        'e': {'class_type': 'VAEEncode', 'inputs': {'pixels': ['i', 0], 'vae': ['2', 2]}},
        '3': {'class_type': 'CLIPTextEncode', 'inputs': {'text': prompt, 'clip': ['2', 1]}},
        '4': {'class_type': 'CLIPTextEncode', 'inputs': {'text': negative, 'clip': ['2', 1]}},
        '5': {'class_type': 'KSampler', 'inputs': {'seed': seed, 'steps': 28, 'cfg': 7.0, 'sampler_name': 'euler',
                                                   'scheduler': 'simple', 'denoise': denoise, 'model': ['2', 0],
                                                   'positive': ['3', 0], 'negative': ['4', 0], 'latent_image': ['e', 0]}},
        '7': {'class_type': 'VAEDecode', 'inputs': {'samples': ['5', 0], 'vae': ['2', 2]}},
        '8': {'class_type': 'SaveImage', 'inputs': {'filename_prefix': 'genart_pixel', 'images': ['7', 0]}},
    }


def run(jobs):
    """jobs: [(workflow, out_path)]. Queues them all, saves each result, returns the failures."""
    left = {}
    for wf, out in jobs:
        left[_post('/prompt', {'prompt': wf})['prompt_id']] = out
    failed = []
    while left:
        time.sleep(1.0)
        for pid in list(left):
            h = _get('/history/' + pid)
            if pid not in h:
                continue
            out = left.pop(pid)
            if h[pid].get('status', {}).get('status_str') == 'error':
                failed.append((out, json.dumps(h[pid]['status'])[:400]))
                continue
            for o in h[pid]['outputs'].values():
                for im in o.get('images', []):
                    data = urllib.request.urlopen(HOST + '/view?' + urllib.parse.urlencode(im)).read()
                    os.makedirs(os.path.dirname(out), exist_ok=True)
                    open(out, 'wb').write(data)
    return failed


def stage_input(path, name):
    """Copy a picture to where ComfyUI's LoadImage can see it."""
    shutil.copyfile(path, os.path.join(COMFY_INPUT, name))
    return name
