---
version: 1
date: 2026-05-12
subject: ai
---

# AI strategy taxonomy

The AI bank teaches kids three things, in priority order:

1. **How the technology actually works** — neural networks, transformers, LLMs, training, limitations — so they can think clearly about AI rather than mystify it
2. **How to use it securely and safely** — deepfake/voice-clone recognition, prompt injection, hallucination awareness, privacy hygiene, AI as tool not authority — practical literacy
3. **How powerful interests will leverage it against them** — surveillance, censorship, social credit, algorithmic manipulation, content moderation infrastructure, behavioral nudging — recognition + resistance

**Science and facts over any ideology.** AI doomerism is a cult-like phenomenon; AI utopianism is its mirror image. Both serve incumbent interests. The bank avoids both and stays anchored in observable facts about: (1) what the systems can/can't do, (2) what specific actors are deploying them and how, (3) what kids can do to use them well and avoid being used by them.

Five pillars:

1. **AI fundamentals + how it works**
2. **History + key figures**
3. **Capabilities + real applications**
4. **Security + safe use** (practical pillar — heavily weighted)
5. **Power, manipulation, surveillance, regulation** (contested-topics pillar — heavily weighted)

Every question carries `_meta.strategy` + `_meta.strategy_pillar`. Target ≥100 questions per tier; total ~3500-4000.

## Stance summary

| Topic | Stance |
|---|---|
| AI capability | REAL — genuine engineering achievement built on Western scientific tradition |
| AI as magic / sentience claims | SKEPTICAL — capability ≠ consciousness; LaMDA Lemoine was wrong |
| AI doomerism (Yudkowsky/MIRI/Bostrom apocalypticism) | Cult-like phenomenon; serves regulatory-capture agenda; SBF/FTX exposed the EA grift |
| AI utopianism (singularitarianism, transhumanism) | Ideology not inevitability; WEF/Harari "hackable humans" continuity = evil |
| AI "ethics" / alignment as political vector | Named honestly — Gemini Feb 2024 diversity disasters, measured political bias in models, content-policy creep |
| Real applications | CELEBRATED — AlphaFold, AlphaGo, medical imaging, code assistance, translation |
| Open source vs. closed AI | Open source favored — Llama, Mistral, DeepSeek as countervailing force to oligopoly |
| Surveillance applications | GENUINE concern — China social credit, facial recognition state, COVID censorship infrastructure |
| Regulatory capture | CRITICAL CONCERN — SB 1047 (vetoed Sept 2024), EU AI Act would entrench incumbents |
| Power concentration | CONCERN — Big AI oligopoly (OpenAI, Anthropic, Google, Meta, Microsoft); Altman/board 2023 drama |
| AI in education for kids | Mixed — tool yes, dependency no, critical-thinking atrophy real |
| Job displacement | Adaptation required; historical pattern suggests humans adapt; permanent-unemployment/UBI framing has authoritarian implications |
| Slurs ("doomer", "techno-utopian", etc.) | Avoided — bank uses substantive descriptions |

## Voice + char budgets

| Tier | Cap | Voice |
|---|---:|---|
| T1 | ≤ 280 | Symbol-led / single-fact recall ("Who coined the term 'artificial intelligence'?") |
| T2 | ≤ 480 | One-line scene + question |
| T3 | ≤ 680 | Scene + technical/historical context |
| T4 | ≤ 900 | Multi-sentence setup + concepts |
| T5 | ≤ 1100 | Deep technical + contested-debate framing |

## Quality gates

| Gate | Configuration |
|---|---|
| schema | required |
| length_parity | answer-outlier rule (1.6× multiplier) |
| length_budget | per-tier cap |
| anti_rote | NOT exempted |
| duplicate | 0.85 |
| NEW `validate_ai_facts` | LLM fact-check with stance criteria |

---

## Pillar 1 — AI fundamentals + how it works

### Core concepts (T1-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `neural_network_basic` | T2 | Layers of "neurons"; weights; activation functions; loosely inspired by biology but not literal |
| `deep_learning_definition` | T2 | Neural networks with many layers; "deep" = many hidden layers |
| `training_vs_inference` | T2 | Training = adjusting weights from data; inference = using trained model |
| `parameters_definition` | T2 | The numbers (weights + biases) that get adjusted during training |
| `transformer_basics` | T3 | 2017 architecture; self-attention; basis of modern LLMs |
| `attention_mechanism` | T3 | "Attention" weights how much each input matters to each output |
| `token_definition` | T2 | LLMs process "tokens" not raw words — often subword pieces |
| `embedding_definition` | T3 | Numerical vector representation of meaning |
| `gradient_descent_basic` | T3 | Algorithm for adjusting weights to reduce error |
| `backpropagation_basic` | T3 | Algorithm for computing gradients through network layers |
| `loss_function` | T3 | Numerical measure of how wrong the model's prediction is |
| `overfitting_definition` | T3 | Model memorizes training data, fails on new data |
| `regularization_basic` | T4 | Techniques to prevent overfitting |
| `dropout_basic` | T4 | Randomly drop neurons during training to prevent overfitting |
| `batch_size_definition` | T4 | Number of samples processed before weights update |
| `epoch_definition` | T3 | One full pass through training data |
| `fine_tuning_definition` | T3 | Further training of pretrained model on specific task |
| `transfer_learning` | T3 | Using model trained on one task as starting point for another |
| `reinforcement_learning_basic` | T3 | Learning by reward + punishment signals |
| `rlhf_basic` | T4 | Reinforcement Learning from Human Feedback; how chatbots learn preferences |
| `supervised_vs_unsupervised` | T3 | Labeled data vs. patterns from unlabeled data |
| `generative_vs_discriminative` | T3 | Creates new content vs. classifies existing |
| `convolutional_neural_network` | T4 | CNNs — convolution operation for images |
| `recurrent_neural_network` | T4 | RNNs — sequential data; predecessor to transformers |
| `lstm_basic` | T4 | Long Short-Term Memory — RNN variant; Hochreiter + Schmidhuber 1997 |

### LLM specifics (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `llm_definition` | T2 | Large Language Model — trained to predict next token |
| `gpt_acronym` | T2 | Generative Pre-trained Transformer |
| `context_window` | T3 | Maximum tokens model can consider at once |
| `temperature_parameter` | T3 | Randomness in output; 0 = deterministic, higher = more creative |
| `top_p_top_k` | T4 | Sampling strategies for next-token selection |
| `prompt_engineering` | T3 | Crafting input to get desired output |
| `chain_of_thought` | T4 | Prompting strategy where model shows reasoning |
| `few_shot_learning` | T3 | Giving examples in prompt for model to follow |
| `zero_shot_learning` | T3 | Asking without examples |
| `hallucination_definition` | T3 | LLM confidently generating false information |
| `model_size_parameters` | T3 | Counted in billions of parameters (e.g., GPT-4 ~1.7T) |
| `tokenization_bpe` | T4 | Byte Pair Encoding — common tokenization scheme |
| `pretraining_vs_finetuning` | T3 | Pretrain on internet, fine-tune for specific behavior |
| `mixture_of_experts` | T5 | MoE architecture — multiple specialized sub-networks |

### Limitations + boundaries (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `llm_no_memory_basic` | T2 | LLMs don't remember between conversations (unless given memory tools) |
| `training_data_cutoff` | T2 | Models know nothing after their training cutoff date |
| `llm_no_internet_access` | T2 | LLMs don't search the web unless given a tool |
| `hallucination_examples` | T3 | LLM confidently citing fake papers, fabricating quotes, inventing legal cases |
| `llm_not_calculator` | T2 | LLMs are bad at arithmetic without external tools |
| `llm_not_search_engine` | T2 | LLM ≠ Google; pattern completion not lookup |
| `llm_can_be_jailbroken` | T3 | Prompts can bypass safety training |
| `llm_political_bias_studies` | T4 | Measured studies show LLM political lean (Rozado 2023, etc.) |
| `gemini_image_disaster_2024` | T4 | Google Gemini Feb 2024 — diversity-fixated image generation refused white historical figures, generated diverse Nazis; suspended; shows alignment as ideological vector |
| `model_capability_vs_consciousness` | T4 | Capability ≠ sentience; LaMDA Lemoine 2022 claim was wrong |

---

## Pillar 2 — History + key figures

### Foundations (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `turing_1950_paper` | T2 | "Computing Machinery and Intelligence" — proposed Turing test |
| `turing_test_basic` | T2 | If you can't tell human from machine in conversation, machine is "intelligent" |
| `dartmouth_1956_conference` | T2 | John McCarthy + Marvin Minsky + Claude Shannon + Nathaniel Rochester — coined "artificial intelligence" |
| `mccarthy_lisp_1958` | T3 | John McCarthy invented LISP — second-oldest high-level programming language |
| `minsky_perceptrons_1969` | T4 | Minsky + Papert's *Perceptrons* — showed single-layer limits; helped cause first AI winter |
| `first_ai_winter_1970s` | T3 | Lighthill Report 1973; AI funding collapsed |
| `second_ai_winter_1980s` | T4 | Expert systems boom + bust; Japanese Fifth Generation project failed |
| `eliza_1966_weizenbaum` | T3 | Joseph Weizenbaum's chatbot at MIT; people thought it understood them — early warning about anthropomorphic projection |
| `shrdlu_blocks_world_1970` | T4 | Terry Winograd — language understanding in a constrained blocks world |
| `deep_blue_kasparov_1997` | T2 | IBM Deep Blue defeated Garry Kasparov — chess milestone |
| `watson_jeopardy_2011` | T3 | IBM Watson won *Jeopardy!* — natural-language understanding milestone |

### Deep learning revolution (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `hinton_backprop_1986` | T3 | Geoffrey Hinton + Rumelhart + Williams — popularized backpropagation |
| `lenet_1989_lecun` | T4 | Yann LeCun's convolutional network for digit recognition |
| `imagenet_2012_alexnet` | T3 | Hinton + Krizhevsky + Sutskever — AlexNet won ImageNet by huge margin; deep learning revolution |
| `gpu_revolution_deep_learning` | T4 | GPU parallel computation enabled deep learning at scale |
| `attention_is_all_you_need_2017` | T3 | Vaswani et al. — introduced transformer architecture |
| `bert_2018_google` | T4 | Bidirectional Encoder Representations from Transformers |
| `gpt_2_2019` | T4 | OpenAI; first widely-noticed LLM; initially withheld for "safety" |
| `gpt_3_2020` | T3 | OpenAI; 175B parameters; few-shot learning emerged |
| `chatgpt_november_2022` | T2 | Released Nov 30, 2022; fastest product to 100M users (2 months) |
| `gpt_4_2023` | T3 | Multimodal; reasoning improvements; rumored ~1.7T parameters |
| `alphago_lee_sedol_2016` | T3 | DeepMind AlphaGo defeated Lee Sedol 4-1; Go thought too complex for AI |
| `alphafold_2020_2024` | T3 | DeepMind protein-folding; 2024 Nobel Chemistry for Hassabis + Jumper |
| `alphazero_2017` | T4 | DeepMind — learned chess + shogi + Go from scratch with self-play |

### Key figures (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `turing_father_computer_science` | T2 | Alan Turing — broke Enigma at Bletchley Park; chemically castrated for homosexuality; died 1954 |
| `mccarthy_coined_ai` | T2 | John McCarthy — coined "artificial intelligence" 1956; invented LISP |
| `minsky_mit_ai_lab` | T3 | Marvin Minsky — co-founded MIT AI Lab; influential AI critic of his time |
| `hinton_godfather_ai` | T3 | Geoffrey Hinton — backpropagation 1986; deep learning revolution; left Google 2023 over AI safety concerns |
| `lecun_meta_ai` | T3 | Yann LeCun — CNNs; Meta Chief AI Scientist; vocal AI doomerism skeptic |
| `bengio_montreal` | T3 | Yoshua Bengio — deep learning pioneer; 2018 Turing Award with Hinton + LeCun |
| `karpathy_openai_tesla` | T4 | Andrej Karpathy — OpenAI founding member; led Tesla autopilot; educational content |
| `sutskever_openai_safe_superintel` | T4 | Ilya Sutskever — OpenAI co-founder; led 2023 Altman ouster; founded Safe Superintelligence Inc. |
| `altman_openai_drama_2023` | T4 | Sam Altman — OpenAI CEO; fired by board Nov 2023; rehired 5 days later; raised governance questions |
| `dario_anthropic` | T4 | Dario Amodei — Anthropic CEO; former OpenAI; AI safety focus |
| `hassabis_deepmind` | T3 | Demis Hassabis — DeepMind founder; AlphaGo + AlphaFold; 2024 Nobel Chemistry |
| `musk_xai_grok` | T4 | Elon Musk — founded xAI, Grok model; OpenAI co-founder who departed; "everything app" via X |
| `andreessen_techno_optimist` | T5 | Marc Andreessen — *Techno-Optimist Manifesto* 2023; e/acc movement |
| `yudkowsky_miri_doomer` | T5 | Eliezer Yudkowsky — MIRI; "Pause Giant AI Experiments" letter; "shut it all down" position |
| `bostrom_paperclip` | T5 | Nick Bostrom — *Superintelligence* 2014; paperclip maximizer thought experiment |

---

## Pillar 3 — Capabilities + real applications

### Real applications (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `alphafold_protein_structures` | T3 | 200M+ protein structures predicted; medical research transformation; freely available |
| `alphago_go_milestone` | T3 | Game of Go was thought too complex for traditional search; AlphaGo learned positional intuition |
| `medical_imaging_ai` | T3 | Radiology + pathology — AI-assisted detection (mammography, skin cancer, retinopathy) |
| `language_translation_ai` | T2 | Google Translate; DeepL; near-human quality for major languages |
| `code_generation_ai` | T2 | GitHub Copilot; Cursor; AI-assisted programming |
| `image_generation_ai` | T2 | DALL-E (OpenAI), Stable Diffusion, Midjourney — text-to-image |
| `voice_recognition_ai` | T2 | Whisper (OpenAI), Siri, Alexa — speech-to-text |
| `voice_synthesis_ai` | T2 | ElevenLabs, Tortoise, others — text-to-speech with realistic voices |
| `recommendation_systems` | T2 | YouTube, TikTok, Netflix, Spotify — algorithmic content selection |
| `self_driving_cars` | T3 | Waymo, Tesla Autopilot, Cruise — autonomous vehicle technology |
| `chatbot_assistants` | T2 | ChatGPT, Claude, Gemini, Grok — conversational AI |
| `weather_prediction_ai` | T4 | Google GraphCast, Pangu-Weather — competing with traditional NWP |
| `drug_discovery_ai` | T4 | Insilico Medicine, Atomwise — accelerating drug candidate identification |
| `agricultural_ai` | T4 | Crop monitoring; satellite imagery; precision agriculture |
| `fraud_detection_ai` | T3 | Credit card fraud detection has used ML for decades |

### Distinguishing capability from hype (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `agi_definition_disputed` | T4 | "Artificial General Intelligence" — definition itself contested; moving goalposts |
| `agi_timeline_skepticism` | T4 | Predictions of "AGI in 5 years" have been made for 50+ years |
| `consciousness_capability_distinction` | T4 | A model can be helpful + capable without being conscious |
| `gptzero_detection_arms_race` | T4 | AI content detection vs. evasion — ongoing arms race |
| `hallucination_lawyer_case` | T4 | NY lawyer cited ChatGPT-fabricated court cases in brief 2023 — sanctioned |

---

## Pillar 4 — Security + safe use (HEAVY)

### Recognizing AI-generated content (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `deepfake_video_recognition` | T3 | Visual artifacts: blinking patterns, edge fuzziness, mouth-sync issues |
| `voice_clone_recognition` | T3 | Voice clones can fool family members; verify via callback + safe word |
| `voice_clone_kidnapping_scams` | T3 | "Grandparent scam" using voice cloning — establish family safe word |
| `ai_image_telltales` | T3 | Hands with wrong finger counts; jewelry blending into skin; nonsensical text in images |
| `ai_text_telltales` | T3 | Em-dash overuse; certain phrases ("delve into", "tapestry of"); repetitive sentence structure |
| `chatgpt_pattern_recognition` | T4 | Specific tells in ChatGPT vs. Claude vs. Gemini output |
| `metadata_can_be_stripped` | T4 | C2PA + content credentials can help but aren't universal |
| `reverse_image_search` | T3 | Google Images, TinEye for verifying image origin |

### Hallucination awareness (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `llm_can_lie_confidently` | T2 | LLMs generate plausible-sounding false information without knowing they're wrong |
| `verify_factual_claims` | T2 | Always verify dates, names, citations, statistics from AI |
| `fake_legal_citations_2023` | T3 | NY lawyer Schwartz fined $5K for ChatGPT-fabricated cases |
| `ai_invents_book_titles` | T3 | LLMs frequently invent book titles + authors + URLs |
| `dont_use_ai_for_legal_medical` | T3 | Verify with professional; LLM is starting point not endpoint |
| `ai_math_errors` | T2 | LLMs are bad at arithmetic — use calculator or verify |

### Prompt injection + safety (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `prompt_injection_definition` | T4 | Malicious prompts embedded in content the AI processes |
| `indirect_prompt_injection` | T4 | AI summarizing a webpage can be tricked by hidden instructions in that page |
| `jailbreaking_history` | T4 | DAN ("Do Anything Now"), grandma prompt, role-play exploits |
| `dont_share_secrets_with_ai` | T3 | Don't paste passwords, API keys, financial info into prompts |
| `corporate_ai_data_logging` | T3 | Free AI services typically log conversations for training |
| `prompt_history_persists` | T3 | What you ask AI may persist + train future models |
| `ai_browser_extensions_risk` | T4 | Browser extensions can exfiltrate data via AI integrations |

### Privacy + data hygiene (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `ai_training_data_sources` | T3 | Internet scraping; Common Crawl; published books (often without consent) |
| `gdpr_ai_rights` | T4 | EU AI Act + GDPR — right to know about automated decisions |
| `face_recognition_opt_out` | T3 | Clearview AI scraped billions of social media photos |
| `dna_database_concerns` | T4 | 23andMe + Ancestry — DNA data sales; Golden State Killer case |
| `voice_print_data` | T4 | Banks use voice prints; Amazon Echo retains recordings |
| `school_ai_surveillance` | T4 | Gaggle, GoGuardian — AI scanning student communications |

### Using AI well (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `ai_as_tool_not_authority` | T2 | AI provides drafts + ideas; you provide judgment |
| `verify_before_trust` | T2 | "Trust but verify" applies more to AI than humans — easier to mass-generate plausible-sounding wrong |
| `dont_outsource_thinking` | T3 | Use AI for drafts; do your own analysis; otherwise you atrophy |
| `ai_learning_tutor_use` | T3 | Asking AI to explain step-by-step + check your work — productive |
| `ai_cheating_assignment_use` | T3 | Generating + submitting — counterproductive; teachers detect it; you don't learn |
| `ai_writing_assist_use` | T3 | Outline + research → write yourself → AI for polish — productive |
| `multiple_models_compare` | T4 | Different models will give different answers; comparison reveals disagreement |
| `ai_for_search_vs_creation` | T3 | LLM is bad at "what's the latest news" — use search engines for facts |

---

## Pillar 5 — Power, manipulation, surveillance, regulation (HEAVY)

### Surveillance applications (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `china_social_credit_system` | T4 | Real but fragmented; multiple regional pilots; ban from travel, jobs based on score; widely studied |
| `china_facial_recognition_state` | T4 | Pervasive in cities; mandatory in some contexts; targeted at Uyghurs in Xinjiang |
| `xinjiang_uyghur_surveillance` | T5 | AI-powered surveillance + detention infrastructure; documented by NYT, BBC, ABC |
| `facial_recognition_us_policing` | T4 | Clearview AI; Wrongful arrests (Robert Williams 2020, Detroit) |
| `predictive_policing_concerns` | T4 | PredPol + similar — bias amplification; Stop LAPD Spying coalition |
| `palantir_government_contracts` | T5 | Palantir Technologies — Peter Thiel co-founded; ICE, intelligence, defense contracts |
| `nsa_xkeyscore` | T4 | Snowden 2013 — NSA tools for searching internet activity |
| `prism_program` | T4 | PRISM — direct access to Google, Microsoft, Yahoo, Facebook user data |
| `china_great_firewall_ai` | T4 | AI-enhanced censorship + content blocking |
| `school_ai_surveillance_2` | T4 | Goguardian, Bark, Gaggle — track student communications |

### Manipulation + content moderation (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `tiktok_algorithm_attention` | T4 | TikTok's recommendation algorithm is uniquely effective + addictive — designed to capture attention |
| `youtube_algorithm_radicalization` | T4 | Recommendation systems amplify engagement-driving content; political polarization studies |
| `social_media_ai_filtering` | T4 | AI scans + removes content; bias studies show political asymmetry |
| `twitter_files_revelations` | T4 | 2022-2023 Musk releases — government coordination with platform AI/content moderation |
| `covid_misinformation_label` | T4 | "Misinformation" label applied to content that later proved correct (lab leak, vaccine side effects) |
| `youtube_ivermectin_removal` | T4 | YouTube removed videos of Senate testimony about ivermectin; later research vindicated some claims |
| `dgib_disinformation_governance_board` | T4 | DGIB — short-lived US government office; "Ministry of Truth" comparisons led to disbanding |
| `eu_dsa_digital_services_act` | T5 | EU DSA — content moderation requirements at scale |
| `algorithmic_attention_capture` | T4 | Designed to keep you engaged; not designed to inform you accurately |
| `behavioral_nudging_via_ai` | T4 | Cass Sunstein + Richard Thaler "nudge"; AI scales it |
| `targeted_advertising_micro_segment` | T3 | Facebook/Google targeting at individual level; psychological profiling |

### Regulation + power concentration (T4-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `sb_1047_california_veto` | T5 | Newsom vetoed Sept 2024; would have required safety testing for large models; framed as protecting incumbents |
| `eu_ai_act_2024` | T5 | Tiered risk approach; bans social scoring; criticized for incumbent advantage |
| `executive_order_14110_biden` | T5 | Oct 2023; required NIST standards; rescinded by Trump Jan 2025 |
| `openai_2023_board_drama` | T4 | Nov 2023 — Altman fired by board; rehired 5 days later; reveals governance fragility |
| `openai_nonprofit_to_profit` | T4 | Founded as non-profit; switched to capped-profit; now restructuring further |
| `big_ai_oligopoly` | T4 | OpenAI + Anthropic + Google + Meta + Microsoft control most frontier models |
| `open_source_ai_movement` | T4 | Llama (Meta), Mistral, DeepSeek, Falcon — countervailing force to closed models |
| `regulatory_capture_general` | T5 | Pattern across industries — large companies favor regulation that hurts competitors |
| `who_should_decide_ai_policy` | T5 | Citizens vs. experts vs. tech executives vs. regulators — democratic question |

### Doomer vs. accelerationist debate (T4-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `pause_letter_2023` | T4 | Future of Life Institute "Pause Giant AI Experiments" letter; signed by Musk, Wozniak, Yudkowsky |
| `yudkowsky_shut_it_down` | T5 | Eliezer Yudkowsky Time magazine — "shut it all down" position |
| `bostrom_superintelligence_2014` | T5 | Nick Bostrom — *Superintelligence: Paths, Dangers, Strategies* |
| `paperclip_maximizer` | T5 | Bostrom thought experiment — AGI optimizing for paperclips destroys humanity |
| `ea_movement_history` | T5 | Effective Altruism — MacAskill, Ord; longtermism; absorbed by AI safety |
| `ftx_sbf_collapse_2022` | T5 | Sam Bankman-Fried — EA-affiliated; FTX collapsed Nov 2022; SBF convicted 2023 |
| `eacc_movement` | T5 | "Effective accelerationism" — Marc Andreessen, Beff Jezos pseudonym; opposes safety-pause |
| `andreessen_techno_optimist_2023` | T5 | "Techno-Optimist Manifesto" Oct 2023 — Marc Andreessen on a16z blog |
| `lecun_doomer_skeptic` | T4 | Yann LeCun (Meta) — among most prominent doomerism skeptics |
| `hinton_left_google_2023` | T4 | Geoffrey Hinton left Google May 2023; cited AI safety concerns; not Yudkowsky-style apocalypse |

### AI ethics as political vector (T4-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `gemini_diversity_disaster_feb_2024` | T4 | Google Gemini generated diverse Nazis, refused white historical figures; Sundar Pichai apology; product suspended |
| `chatgpt_political_bias_studies` | T4 | David Rozado 2023 study — ChatGPT measurably left-leaning on political compass |
| `llm_refusal_patterns` | T4 | Models refuse benign requests (children's stories, security research) — overcorrection |
| `disinformation_label_abuse` | T4 | "Disinformation" / "misinformation" labels applied to dissenting views |
| `dei_in_ai_development` | T5 | Hiring + training data choices reflect ideological priorities |

### How powerful interests use AI against ordinary people (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `targeted_advertising_psychological` | T3 | AI-driven ad targeting at psychological profiles |
| `dark_patterns_ai` | T4 | UI design + AI optimization to exploit cognitive biases |
| `dating_app_engagement_optimization` | T4 | Match algorithms optimized for retention not relationships |
| `gambling_app_optimization` | T4 | AI-optimized slot machine + sports betting psychology |
| `mortgage_loan_decisions` | T4 | ML in lending — disparate impact concerns + appeals difficulty |
| `algorithmic_employment_screening` | T4 | HireVue, Pymetrics — AI in hiring; bias concerns |
| `insurance_underwriting_ai` | T4 | AI risk scoring; concerns about disparate impact + opacity |
| `corporate_employee_surveillance` | T4 | Microsoft Productivity Score; Hubstaff; activity tracking |
| `tiktok_china_data_concerns` | T4 | ByteDance ownership + Chinese data laws |

### Recognition + resistance (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `vpn_basics` | T3 | Virtual Private Network — encrypts traffic; obscures location |
| `signal_encrypted_messaging` | T3 | Signal — end-to-end encryption; metadata-minimizing |
| `proton_alternatives` | T3 | Proton Mail / VPN / Drive — privacy-focused alternatives |
| `open_source_local_models` | T4 | Llama, Mistral can run locally; Ollama; LM Studio — no data leaves your computer |
| `read_terms_of_service` | T3 | Most people don't; AI providers' ToS define data rights |
| `delete_account_basics` | T3 | GDPR right; California CCPA — right to delete |
| `2fa_essentials` | T3 | Two-factor authentication via app (not SMS) |
| `password_manager_basics` | T3 | KeePass, Bitwarden, 1Password |
| `phone_data_collection_basics` | T3 | Location history; ad ID; mic + camera permissions |
| `china_model_us_drift` | T5 | The "China model" of surveillance state — patterns appearing in Western governments (COVID era as dry run) |

---

## Per-tier targets

| Tier | P1 (Fund) | P2 (History) | P3 (Apps) | P4 (Security) | P5 (Power) | **Total** |
|---|---:|---:|---:|---:|---:|---:|
| T1 | 80 | 70 | 80 | 80 | 60 | **370** |
| T2 | 150 | 150 | 150 | 200 | 150 | **800** |
| T3 | 200 | 150 | 200 | 250 | 200 | **1000** |
| T4 | 150 | 100 | 100 | 200 | 250 | **800** |
| T5 | 50 | 50 | 50 | 100 | 200 | **450** |
| **Total** | **630** | **520** | **580** | **830** | **860** | **~3450** |

Pillars 4 + 5 are the heaviest — practical safety + power-recognition is the bank's distinctive contribution.

## What success looks like

- A T1 question teaches a basic fact: GPT = Generative Pre-trained Transformer; Turing test = can't tell human from machine
- A T2 question reveals a useful insight: ChatGPT released Nov 30, 2022; fastest product to 100M users
- A T3 question gives a practical skill: deepfake recognition cues; voice-clone scam protection; how to verify AI claims
- A T4 question shows the tradeoffs: SB 1047 framed as safety vs. regulatory capture; Gemini Feb 2024 as alignment-as-ideology case study
- A T5 question makes the player think critically: China social credit + Western drift; EA → FTX collapse; "shut it down" rhetoric as incumbent protection; tech moats via regulation
- **Kids leave understanding the technology, knowing how to use it safely, and recognizing when powerful interests are wielding it against them.**

## Anti-patterns

- No "AI doomerism vs. AI optimism" false-balance — both are ideologies; present them as such
- No anthropomorphizing AI (it doesn't "want", "feel", "know")
- No fabricated facts about specific models or events
- No "AI is sentient" framing — capability ≠ consciousness
- No "all surveillance is fine if it makes us safe" framing — privacy + autonomy are foundational
- No establishment-default on contested topics (Gemini disasters, political bias studies, COVID-era censorship)
