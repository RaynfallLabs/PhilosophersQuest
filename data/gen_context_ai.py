#!/usr/bin/env python3
"""
Add educational 'context' fields to every question in ai.json.
Each context is a 2-3 sentence explanation shown when the player answers wrong.
"""

import json
import os

CONTEXTS = {
    # =========================================================================
    # TIER 1 — Basics (100 questions)
    # =========================================================================
    "What does AI stand for?":
        "AI stands for Artificial Intelligence — 'artificial' because it's made by humans, and 'intelligence' because it can do smart things like recognize patterns and make decisions. It's not a brain in a jar; it's clever software running on regular computers.",

    "Can computers learn from experience?":
        "Yes! Machine learning lets computers improve by analyzing past results, kind of like how you get better at a game the more you play. They don't 'remember' the way you do — they adjust mathematical patterns inside themselves.",

    "What is a robot?":
        "A robot is a physical machine built to carry out tasks — from assembling cars to vacuuming your floor. Not all robots use AI (some just follow fixed instructions), and not all AI lives inside a robot (most AI is just software on a screen).",

    "Who made ChatGPT?":
        "ChatGPT was created by OpenAI, an AI research company founded in 2015 in San Francisco. It launched in November 2022 and became one of the fastest-growing apps in history, reaching 100 million users in just two months.",

    "Can AI write stories?":
        "Absolutely — large language models can generate poems, short stories, and even novels by predicting one word at a time. The results can be surprisingly creative, though AI doesn't truly 'understand' the story the way a human author does.",

    "Can AI play chess?":
        "Yes, and it's been doing it since the 1990s. IBM's Deep Blue beat world champion Garry Kasparov in 1997, and modern chess engines like Stockfish are so powerful that no human can beat them.",

    "What is a computer program?":
        "A computer program is a set of step-by-step instructions written in a programming language that tells a computer exactly what to do. Everything from your calculator app to a massive AI model is ultimately a program.",

    "Can AI draw pictures?":
        "Yes! Tools like DALL-E, Midjourney, and Stable Diffusion generate images from text descriptions. They learned by studying millions of pictures and their captions, so they can remix visual concepts in brand-new ways.",

    "What does a search engine like Google do?":
        "A search engine crawls billions of web pages, indexes their content, and uses algorithms (including AI) to rank the most relevant results for your query. It's like a super-fast librarian for the entire internet.",

    "What is data?":
        "Data is any information a computer can store and process — numbers, text, images, sounds, you name it. AI is hungry for data because that's what it learns from, much like you learn from books and experiences.",

    "What is a chatbot?":
        "A chatbot is a program designed to have conversations with people, usually through text. Simple ones follow scripted responses, while advanced ones (like ChatGPT or Claude) use large language models to generate natural-sounding replies.",

    "Can AI recognize faces in photos?":
        "Yes — facial recognition AI analyzes features like the distance between your eyes, nose shape, and jawline to identify people. Your phone uses this technology every time you unlock it with your face.",

    "What is an algorithm?":
        "An algorithm is like a recipe for a computer: a clear, ordered set of steps to solve a problem. Everything from sorting a list of names alphabetically to recommending your next YouTube video is powered by algorithms.",

    "What device do you use to talk to Siri or Alexa?":
        "You talk to Siri through an iPhone, iPad, or Mac, and to Alexa through an Amazon Echo smart speaker or the Alexa app. These devices have microphones that send your voice to AI servers for processing.",

    "Can AI help translate languages?":
        "Yes — apps like Google Translate use AI to convert text and speech between over 100 languages in real time. Modern translation AI uses neural networks that understand context, making translations much more natural than older word-by-word methods.",

    "What is the internet?":
        "The internet is a worldwide network of billions of connected computers and devices sharing information. It's not one single thing — it's a vast web of cables, satellites, and wireless signals linking everything from your phone to massive data centers.",

    "What is a voice assistant?":
        "A voice assistant is AI software that listens to your spoken commands and responds helpfully — setting alarms, answering questions, or playing music. Siri, Alexa, and Google Assistant are the most well-known ones.",

    "Can AI help doctors?":
        "Yes — AI can analyze X-rays, MRIs, and CT scans to spot diseases sometimes faster and more accurately than human eyes. It's also used to predict patient outcomes and help discover new drugs.",

    "What is Siri?":
        "Siri is Apple's voice assistant, launched in 2011 as one of the first mainstream AI assistants built into a smartphone. It can answer questions, send messages, set reminders, and control smart home devices using natural language.",

    "What is Alexa?":
        "Alexa is Amazon's voice assistant, primarily used through Echo smart speakers launched in 2014. It can play music, control smart home gadgets, shop online, and answer questions — all by listening to your voice.",

    "Can AI recommend movies you might like?":
        "Yes! Netflix, YouTube, and Spotify all use recommendation algorithms that analyze what you've watched or listened to before. They find patterns in your preferences and match them with similar content other people enjoyed.",

    "What does a computer need to learn?":
        "Computers learn from data — thousands or millions of examples that show it what correct answers look like. The more relevant, high-quality data it gets, the better it can spot patterns and make accurate predictions.",

    "Can AI make music?":
        "Yes — AI can compose melodies, generate beats, and even mimic the style of famous musicians. It learns musical patterns from huge libraries of songs, though whether AI music is truly 'creative' is still hotly debated.",

    "What is a smart home device?":
        "A smart home device is a gadget connected to the internet that you can control remotely — think smart lights, thermostats, or locks. Many use AI voice assistants so you can just say 'turn off the lights' instead of flipping a switch.",

    "Who is more creative, humans or AI?":
        "Humans are still the champions of genuine creativity — we can imagine entirely new ideas, feel emotions, and draw on life experiences. AI can generate impressive content, but it's remixing patterns from its training data rather than truly inventing from nothing.",

    "Can AI understand human emotions perfectly?":
        "Not perfectly — AI can detect clues like facial expressions, tone of voice, and word choice to guess how someone feels. But it doesn't actually experience emotions itself; it's pattern-matching, not true empathy.",

    "What is a selfie filter that changes your face an example of?":
        "Selfie filters use AI image processing to detect your face in real time, map its features, and overlay effects like dog ears or age changes. It's computer vision working at lightning speed right on your phone's camera.",

    "Can AI beat humans at board games?":
        "Yes — AI has beaten world champions at chess, Go, and many other games. DeepMind's AlphaGo shocked the world in 2016 by defeating Go champion Lee Sedol in a game once thought too complex for computers.",

    "What is spam filtering in email?":
        "Spam filters use AI to analyze incoming emails and sort junk messages away from your inbox. They learn from patterns like suspicious links, weird sender addresses, and spammy phrases to catch unwanted mail.",

    "What is autocomplete on your phone?":
        "Autocomplete uses a small AI model right on your phone to predict what word you'll type next based on context. It learns from your typing habits over time, which is why it gets better at guessing your common phrases.",

    "Is AI alive?":
        "No — AI is software running on hardware. It doesn't eat, breathe, grow, or have feelings. Even when AI sounds very human-like in conversation, it's processing math and statistics, not experiencing consciousness.",

    "Can AI drive cars?":
        "Yes — self-driving cars use a combination of cameras, radar, lidar, and AI to perceive roads and make driving decisions. Companies like Tesla, Waymo, and Cruise are developing this technology, though fully autonomous driving is still being perfected.",

    "What is a computer's brain called?":
        "The CPU (Central Processing Unit) is often called the computer's brain because it executes instructions and does calculations. For AI work specifically, GPUs (Graphics Processing Units) are often more important because they can handle many calculations at once.",

    "What should you do if AI gives you wrong information?":
        "Always check AI-generated answers against trusted sources like textbooks, reputable websites, or experts. AI can sound very confident even when it's wrong — a phenomenon called 'hallucination' — so healthy skepticism is a superpower.",

    "Can AI tell the difference between a cat and a dog in photos?":
        "Yes — image classification AI has been great at this for over a decade. It learns by studying thousands of labeled cat and dog photos, picking up on features like ear shape, snout length, and body proportions.",

    "What kind of AI do video games often use?":
        "Video games use AI to control non-player characters (NPCs) — the enemies, allies, and bystanders you interact with. This AI follows behavior scripts and decision trees to make characters seem believable and challenging.",

    "What is the most important thing AI needs to learn?":
        "AI needs lots of examples and data to learn effectively. Just like you'd struggle to learn a language from only three sentences, AI needs massive amounts of high-quality examples to find reliable patterns.",

    "What does GPS navigation use to find the best route?":
        "GPS navigation apps use algorithms — specifically graph-search algorithms — to evaluate thousands of possible routes and pick the fastest one. They factor in distance, traffic data, road closures, and speed limits.",

    "Can you ask AI to help you with homework?":
        "Yes, AI can be a great study tool — it can explain concepts, check your work, and suggest approaches. But the key is to learn from it rather than just copy answers, because understanding the material is what actually helps you grow.",

    "What company makes the iPhone's Siri?":
        "Apple develops Siri as part of its iOS ecosystem. Siri was originally created by a startup called SRI International, which Apple acquired in 2010 before launching Siri on the iPhone 4S in 2011.",

    "What is a computer virus?":
        "A computer virus is a malicious program that can copy itself and spread to other computers, potentially damaging files or stealing information. Unlike biological viruses, computer viruses are deliberately written by people with bad intentions.",

    "Can AI help people who cannot see?":
        "Yes — AI can describe images aloud, read text from signs and documents, and even help navigate environments. Apps like Be My Eyes use AI to give visually impaired people real-time descriptions of the world around them.",

    "What is YouTube's recommendation system?":
        "YouTube's recommendation AI analyzes your watch history, likes, and viewing time to suggest videos you'll probably enjoy. It's responsible for over 70% of what people watch on the platform — it's incredibly powerful at keeping you engaged.",

    "What is the difference between a robot and AI?":
        "A robot is a physical machine with moving parts that can interact with the real world. AI is software that processes information intelligently. A robot can use AI as its 'brain,' but AI can also exist without any physical body at all.",

    "Can AI help predict the weather?":
        "Yes — weather forecasting relies heavily on AI analyzing massive amounts of data from satellites, weather stations, and ocean sensors. Modern AI weather models can sometimes outperform traditional physics-based forecasting methods.",

    "What does a spell checker use to find mistakes?":
        "Spell checkers compare your words against a dictionary using rules and AI algorithms. Modern ones go beyond simple dictionary lookups — they use language models to catch grammar errors and suggest better phrasing based on context.",

    "What year was the first electronic computer built?":
        "ENIAC, generally considered the first general-purpose electronic computer, was completed in 1945 at the University of Pennsylvania. It weighed 30 tons and filled an entire room — your smartphone is millions of times more powerful.",

    "What is coding?":
        "Coding (or programming) is writing instructions in a language computers understand, like Python, JavaScript, or C++. Every app, website, and AI system you use exists because someone wrote code to create it.",

    "Can AI think exactly like a human?":
        "No — AI processes information through mathematical operations on numbers, while human thinking involves biology, emotions, and consciousness. AI can mimic human-like responses impressively, but what's happening 'under the hood' is completely different.",

    "What is a password used for?":
        "A password is a secret string of characters that proves your identity to a computer system, keeping your accounts safe from unauthorized access. Strong passwords use a mix of letters, numbers, and symbols to make them hard to guess.",

    "What is facial recognition?":
        "Facial recognition is AI technology that identifies or verifies a person by analyzing their facial features from a photo or video. It maps unique characteristics like the geometry of your face and compares them against a database.",

    "What is the name of Google's voice assistant?":
        "It's called Google Assistant, launched in 2016. It's built into Android phones, Google Home speakers, and many other devices, and it can answer questions, control smart devices, and have back-and-forth conversations.",

    "Can AI create new recipes for cooking?":
        "Yes — AI can analyze thousands of existing recipes to understand flavor combinations and cooking techniques, then generate brand-new recipes. Some results are delicious; others are hilariously strange, like chocolate-covered pizza with pickles.",

    "What happens when you say 'Hey Siri' to an iPhone?":
        "A small, always-listening AI on your phone detects the specific 'Hey Siri' sound pattern and wakes up the full voice assistant. Your voice command is then processed (often using cloud AI) to figure out what you're asking.",

    "What is a drone?":
        "A drone is an unmanned flying machine — essentially a remote-controlled or autonomous aircraft. Many modern drones use AI for features like obstacle avoidance, autonomous flight paths, and object tracking.",

    "Can AI help scientists discover new medicines?":
        "Yes — AI can analyze billions of potential molecular compounds far faster than humans, predicting which ones might make effective drugs. DeepMind's AlphaFold, for example, revolutionized biology by predicting protein structures.",

    "What does 'training' an AI mean?":
        "Training means feeding an AI system lots of examples so it can learn patterns. It's like studying flashcards — the more examples the AI sees and gets feedback on, the better it gets at recognizing what's what.",

    "What is a pixel?":
        "A pixel is the tiniest individual dot in a digital image — a single point of color. Your phone screen contains millions of them packed so tightly together that they blend into smooth pictures to your eye.",

    "Can AI read handwriting?":
        "Yes — with enough training on handwritten samples, AI can recognize and digitize handwritten text. Post offices have used this technology for decades to sort mail by reading handwritten addresses automatically.",

    "What is WiFi?":
        "WiFi is a wireless technology that uses radio waves to connect your devices to the internet without physical cables. The name doesn't actually stand for anything specific — it was coined as a catchy brand name in 1999.",

    "What does 'virtual' mean in technology?":
        "In tech, 'virtual' means something that exists digitally rather than physically. A virtual meeting happens on screen, not in a room; a virtual assistant lives in software, not in an office chair.",

    "Can AI count objects in a picture?":
        "Yes — computer vision AI can detect and count individual objects in images, even in crowded or complex scenes. This is used in everything from wildlife surveys (counting animals) to manufacturing (counting products on assembly lines).",

    "What does download mean?":
        "Downloading means copying data from a remote server (usually on the internet) to your local device. The opposite — sending data from your device to a server — is called uploading.",

    "What is a touchscreen?":
        "A touchscreen is a display that detects where your finger (or stylus) touches it, letting you interact directly with what's on screen. It uses sensors that track electrical changes when your conductive fingertip makes contact.",

    "Can AI help with recycling?":
        "Yes — AI-powered sorting robots in recycling plants use computer vision to identify different materials (plastic, glass, metal, paper) and sort them with mechanical arms. They can process items faster and more accurately than manual sorting.",

    "What is the cloud in computing?":
        "The 'cloud' means storing and processing data on powerful remote servers accessed via the internet, instead of on your own device. When you save a photo to iCloud or Google Drive, it's actually sitting in a data center somewhere.",

    "What is text-to-speech?":
        "Text-to-speech (TTS) is AI technology that converts written text into spoken words. Modern TTS systems sound remarkably natural — a far cry from the robotic voices of the past — because they're trained on thousands of hours of human speech.",

    "Can AI help farmers grow better crops?":
        "Yes — precision agriculture uses AI to analyze soil conditions, weather patterns, satellite imagery, and sensor data. This helps farmers decide exactly when to water, fertilize, or harvest, reducing waste and boosting yields.",

    "What is an app?":
        "An app (short for application) is a software program designed to perform specific tasks on a phone, tablet, or computer. From games to calculators to social media, apps are how we interact with most of our technology.",

    "What is speech recognition?":
        "Speech recognition is AI technology that converts spoken words into text the computer can process. It's the technology that powers voice assistants — your voice goes in, text comes out, and then more AI figures out what you meant.",

    "Can AI translate between languages in real time?":
        "Yes — real-time translation AI can process spoken words, translate them, and even speak the translation aloud in seconds. Some earbuds and apps now let two people speaking different languages have a natural conversation.",

    "What is a digital assistant?":
        "A digital assistant is an AI program that helps you with everyday tasks — answering questions, setting reminders, managing calendars, and more. Siri, Alexa, Google Assistant, and Cortana are all digital assistants.",

    "What should you never share with an AI chatbot?":
        "Never share passwords, credit card numbers, Social Security numbers, or other sensitive personal information with an AI chatbot. Even if the chatbot seems trustworthy, data can be stored, leaked, or used to train future models.",

    "What is image recognition?":
        "Image recognition is AI that can identify objects, people, text, and scenes within photos or videos. Your phone uses it when you search your photos for 'beach' or 'dog' and it finds matching images automatically.",

    "Can AI help you learn a new language?":
        "Yes — apps like Duolingo use AI to personalize lessons, adjust difficulty, and practice conversation with you. The AI tracks which words you struggle with and reviews them more often, making learning more efficient.",

    "What is a self-driving car?":
        "A self-driving (autonomous) car uses AI, cameras, radar, and lidar to navigate roads without a human driver. The AI must constantly perceive its surroundings, predict what other drivers will do, and make split-second decisions.",

    "Is everything you read on the internet true?":
        "Absolutely not — the internet contains misinformation, outdated content, biased articles, and deliberate lies alongside genuine information. Always cross-check important claims with multiple reliable sources before believing them.",

    "What company made Alexa?":
        "Amazon created Alexa and launched it with the Echo smart speaker in 2014. The name 'Alexa' was chosen partly because the 'x' sound is distinctive and easy for the device's microphones to detect.",

    "Can AI recognize different animal sounds?":
        "Yes — AI trained on audio data can identify species by their calls, from bird songs to whale sounds. Scientists use this technology for wildlife monitoring, tracking endangered species without disturbing them.",

    "What is typing called when the computer finishes your words?":
        "It's called autocomplete (or predictive text). A small language model on your device predicts the most likely next word based on what you've typed so far and your personal typing habits.",

    "What powers most AI systems?":
        "AI systems run on powerful computers packed with specialized processors (especially GPUs) and are trained on enormous amounts of data. The combination of raw computing power and quality data is what makes modern AI possible.",

    "Can AI generate human-like voices?":
        "Yes — AI voice synthesis has become so realistic that it's often hard to tell apart from a real human. This technology powers audiobook narration, voice assistants, and accessibility tools, but it also raises concerns about voice-cloning fraud.",

    "What is a QR code?":
        "A QR (Quick Response) code is a square pattern of black and white modules that encodes information like a URL or text. Your phone's camera uses image processing to scan the pattern and decode the data instantly.",

    "Can AI help with spelling and grammar?":
        "Yes — tools like Grammarly and your phone's built-in checker use AI to catch spelling errors, grammar mistakes, and even suggest better word choices. They analyze sentence structure and context, not just individual words.",

    "What is a video game NPC?":
        "An NPC (Non-Player Character) is any character in a game not controlled by a human player. Game AI gives NPCs behaviors — patrolling guards, chatty shopkeepers, or enemies that chase you — making the game world feel alive.",

    "Can AI work all day without getting tired?":
        "Yes — unlike humans, computers don't need sleep, food, or coffee breaks. An AI can process data 24/7 without any decline in performance, which is one of its biggest advantages for tasks like monitoring security cameras.",

    "What is the main thing that makes AI different from a regular program?":
        "Regular programs follow fixed rules written by a programmer, while AI can learn patterns from data and improve over time. A calculator always follows the same math rules, but an AI can discover new patterns nobody explicitly programmed.",

    "What is an emoji?":
        "An emoji is a small digital icon or image used to express an idea or emotion in text messages and social media. The word comes from Japanese: 'e' (picture) + 'moji' (character). There are now over 3,600 standard emojis.",

    "Can AI help protect the environment?":
        "Yes — AI helps track deforestation from satellite images, monitor endangered species, optimize energy usage in buildings, and predict natural disasters. It's a powerful tool for understanding and protecting our planet.",

    "What is a tablet computer?":
        "A tablet is a portable, flat touchscreen device like an iPad or Samsung Galaxy Tab — bigger than a phone but more portable than a laptop. Tablets use the same kind of processors and software that power smartphones.",

    "Does AI have feelings?":
        "No — even when AI says 'I'm happy to help,' it doesn't actually feel happiness. It generates responses that seem emotional because it learned from human text full of emotions, but there's no inner experience behind the words.",

    "Can AI help find lost pets?":
        "Yes — AI-powered apps can match photos of lost pets against found-pet databases using image recognition. Some services analyze unique markings like nose prints (which are as unique as human fingerprints) to identify specific animals.",

    "What is streaming?":
        "Streaming means watching or listening to content in real time as it's delivered over the internet, rather than downloading the whole file first. Netflix, Spotify, and YouTube all use streaming so you can start enjoying content instantly.",

    "What does USB stand for?":
        "USB stands for Universal Serial Bus — a standard for connecting devices and transferring data. It was designed to be 'universal' so one type of cable could work with many different devices, replacing the mess of different connectors.",

    "Can AI summarize long articles for you?":
        "Yes — AI language models are great at reading long documents and distilling them into shorter summaries. This is incredibly useful for research, news consumption, and anyone drowning in information overload.",

    "What is Bluetooth?":
        "Bluetooth is a short-range wireless technology that lets devices communicate with each other nearby — usually within about 30 feet. It's named after Harald Bluetooth, a Viking king who united Danish tribes, because the technology unites devices.",

    "Can AI identify plants from photos?":
        "Yes — apps like PlantNet and Google Lens use AI image recognition to identify plant species from photos of leaves, flowers, or bark. They compare your photo against databases of millions of plant images.",

    "What is a software update?":
        "A software update is a new version of a program that fixes bugs, patches security holes, or adds new features. Keeping your software updated is one of the most important things you can do for security and performance.",

    "What is a computer mouse used for?":
        "A computer mouse is an input device that moves a pointer on your screen, letting you click buttons, select text, and interact with your computer. It was invented by Douglas Engelbart in 1964 — over 60 years ago!",

    "Can AI help you find your way when you are lost?":
        "Yes — map apps like Google Maps and Apple Maps use AI to calculate routes, predict traffic, suggest detours, and provide turn-by-turn directions. GPS satellites tell the app where you are, and AI figures out the best way to get where you're going.",

    # =========================================================================
    # TIER 2 — Intermediate Concepts (100 questions)
    # =========================================================================
    "What is machine learning?":
        "Machine learning is a branch of AI where computers learn patterns from data instead of being told explicit rules. It's like learning to recognize cats by looking at thousands of cat photos rather than being given a checklist of cat features.",

    "What is training data?":
        "Training data is the collection of examples an AI studies to learn. If you want AI to recognize dogs, you'd feed it thousands of labeled dog images — the quality and diversity of this data directly determines how well the AI performs.",

    "Who is Alan Turing?":
        "Alan Turing was a brilliant British mathematician who is considered the father of computer science and AI. He cracked the Nazi Enigma code in WWII, invented the concept of the universal computing machine, and proposed the famous Turing Test.",

    "What is the Turing Test?":
        "Proposed by Alan Turing in 1950, the Turing Test checks whether a human can tell if they're chatting with a machine or another person. If the machine fools the human, it's considered to have demonstrated human-like intelligence.",

    "What is a neural network inspired by?":
        "Neural networks are inspired by the human brain's structure — billions of neurons connected by synapses. In AI, artificial 'neurons' are mathematical functions connected in layers that pass signals to each other, mimicking how your brain processes information.",

    "What is narrow AI?":
        "Narrow AI (also called weak AI) is designed to do one specific task really well — like playing chess, translating languages, or recommending movies. It's the only kind of AI that actually exists today.",

    "What is general AI?":
        "General AI (AGI) would be a machine that can think, learn, and reason about anything as well as a human can. It doesn't exist yet — and whether it's possible, or when it might arrive, is one of the biggest debates in technology.",

    "What is a prompt in AI?":
        "A prompt is the text or instruction you type into an AI system to tell it what you want. The quality of your prompt matters a lot — a clear, specific prompt usually gets much better results than a vague one.",

    "What is bias in AI?":
        "AI bias happens when a system makes unfair decisions because its training data was skewed or unrepresentative. For example, if a hiring AI was trained mostly on data from male employees, it might unfairly favor male candidates.",

    "What is a large language model?":
        "A large language model (LLM) is an AI trained on enormous amounts of text — books, websites, articles — to understand and generate human language. GPT, Claude, and Gemini are all LLMs with billions of parameters.",

    "What is natural language processing?":
        "Natural Language Processing (NLP) is the field of AI that deals with understanding and generating human language. It powers everything from chatbots and translation to spell checkers and voice assistants.",

    "What is computer vision?":
        "Computer vision is AI that 'sees' — it can understand and interpret images and videos. It's used for facial recognition, self-driving cars, medical image analysis, and even counting the number of people in a crowd.",

    "How do recommendation systems work?":
        "Recommendation systems analyze your past behavior (what you watched, clicked, bought, or liked) to predict what you'll enjoy next. They use techniques like collaborative filtering — finding users similar to you and recommending what they liked.",

    "Should you trust everything an AI tells you?":
        "Never trust AI blindly — it can confidently state false information (called 'hallucination'). Always fact-check important claims, especially for health, legal, or financial topics. Think of AI as a helpful starting point, not the final word.",

    "What is a dataset?":
        "A dataset is an organized collection of data used to train or evaluate AI. It can contain images, text, numbers, or any other type of information — like a giant labeled filing cabinet that AI studies to learn patterns.",

    "What company created the AI assistant Claude?":
        "Claude was created by Anthropic, an AI safety company founded in 2021 by former OpenAI researchers including Dario and Daniela Amodei. Anthropic focuses on building AI that is helpful, harmless, and honest.",

    "What is a self-driving car's biggest challenge?":
        "The hardest part is handling unpredictable real-world situations — a child chasing a ball into the street, unusual road construction, or a plastic bag blowing across the highway. The real world is messier than any training scenario.",

    "What programming language is most popular for AI?":
        "Python is the go-to language for AI and machine learning. It has a simple, readable syntax and a huge ecosystem of libraries like TensorFlow, PyTorch, and scikit-learn that make building AI models much easier.",

    "What is an AI hallucination?":
        "An AI hallucination is when a model generates information that sounds plausible but is completely made up. The AI isn't lying on purpose — it's just very good at producing text that sounds confident, even when it has no basis in reality.",

    "What is the difference between AI and automation?":
        "Automation follows fixed, pre-programmed rules (like a thermostat turning on heat at 68 degrees), while AI can learn, adapt, and handle situations it wasn't explicitly programmed for. AI is flexible; simple automation is rigid.",

    "What is a chatbot used for on websites?":
        "Website chatbots handle common customer questions automatically — like checking order status, answering FAQs, or routing you to the right department. They save companies money while giving customers instant 24/7 support.",

    "What did IBM's Deep Blue do in 1997?":
        "Deep Blue defeated world chess champion Garry Kasparov in a six-game match, becoming the first computer to beat a reigning world champion under standard tournament conditions. It was a landmark moment in AI history.",

    "What is pattern recognition?":
        "Pattern recognition is AI's ability to find recurring structures or regularities in data. It's the core skill behind almost everything AI does — from recognizing your face to detecting credit card fraud to predicting tomorrow's weather.",

    "What is the purpose of a CAPTCHA?":
        "CAPTCHAs (those 'select all traffic lights' puzzles) are designed to tell humans apart from automated bots. Ironically, the image-labeling CAPTCHAs often help train the very AI systems they're designed to block!",

    "What is text generation?":
        "Text generation is AI creating new written content — from stories and articles to code and poetry. Large language models do this by predicting one token (word piece) at a time, building up text that flows naturally.",

    "What is sentiment analysis?":
        "Sentiment analysis is AI that determines whether text expresses positive, negative, or neutral feelings. Companies use it to analyze thousands of product reviews or social media posts to understand what customers think.",

    "How does a voice assistant understand you?":
        "First, speech recognition AI converts your voice into text. Then, natural language processing figures out what you mean. Finally, the assistant generates a response and text-to-speech converts it back into spoken words.",

    "What does GPU stand for?":
        "GPU stands for Graphics Processing Unit. Originally designed to render video game graphics, GPUs turned out to be perfect for AI because they can perform thousands of mathematical calculations simultaneously (in parallel).",

    "Why are GPUs important for AI?":
        "AI training involves massive amounts of matrix math — multiplying huge grids of numbers together. GPUs have thousands of small cores that can do these calculations in parallel, making them up to 100x faster than CPUs for AI workloads.",

    "What is image generation AI?":
        "Image generation AI creates new pictures from text descriptions — you type 'a cat wearing a space helmet' and it produces exactly that. These systems learned the relationship between words and visual concepts from billions of image-text pairs.",

    "What is DALL-E?":
        "DALL-E is an AI image generator created by OpenAI, named as a playful mashup of the artist Salvador Dali and the Pixar robot WALL-E. It can create original images from text prompts and was one of the first widely-used image generation tools.",

    "What is the AI 'black box' problem?":
        "The black box problem means we can see what goes into an AI and what comes out, but we often can't explain exactly how it reached its decision internally. This is concerning for high-stakes applications like medical diagnosis or criminal justice.",

    "What is supervised learning?":
        "In supervised learning, AI trains on labeled examples where the correct answer is provided — like flashcards with questions and answers. The model learns to map inputs to correct outputs by studying thousands of these labeled pairs.",

    "What is unsupervised learning?":
        "In unsupervised learning, AI explores data without any labels or correct answers, discovering hidden patterns on its own. It's like sorting a pile of coins by size, color, and shape without anyone telling you what the categories are.",

    "What was the first AI program generally considered successful?":
        "The Logic Theorist, created in 1956 by Allen Newell and Herbert Simon, proved 38 of the first 52 theorems in a famous math textbook. It was presented at the Dartmouth Conference, where the term 'artificial intelligence' was coined.",

    "What is a deepfake?":
        "A deepfake is AI-generated fake video or audio that makes it look like a real person said or did something they never actually did. The name combines 'deep learning' with 'fake,' and the technology raises serious concerns about misinformation.",

    "What is reinforcement learning?":
        "Reinforcement learning is like training a dog with treats — the AI takes actions, receives rewards for good ones and penalties for bad ones, and gradually learns the best strategy. It's how AI learned to play games like Go and Atari.",

    "What is the main risk of AI bias?":
        "Biased AI can lead to unfair treatment of people based on race, gender, age, or other characteristics. If a loan approval AI was trained on historically biased data, it might unfairly deny loans to certain groups — amplifying real-world inequality.",

    "What is an AI model?":
        "An AI model is a mathematical system that has been trained on data to recognize patterns and make predictions. Think of it as a very complex formula: you put data in one end, and predictions come out the other.",

    "What is data labeling?":
        "Data labeling means adding tags or descriptions to raw data so AI can learn from it. Humans label thousands of images ('this is a cat,' 'this is a dog') to create the training examples that supervised learning needs.",

    "What is optical character recognition (OCR)?":
        "OCR is AI that reads printed or handwritten text from images and converts it to digital text you can edit and search. It's how your phone can scan a document with your camera and turn it into editable text.",

    "What are AI ethics?":
        "AI ethics are guidelines and principles for developing and using AI responsibly — ensuring fairness, transparency, privacy, and accountability. They address questions like: Who's responsible when AI makes a mistake? Should AI replace human jobs?",

    "What is a neural network made up of?":
        "A neural network consists of layers of interconnected nodes (artificial neurons) that process information. Data flows through an input layer, gets transformed through hidden layers, and produces results at the output layer.",

    "What is generative AI?":
        "Generative AI creates new content — text, images, music, code, or video — that didn't exist before. Unlike AI that classifies or predicts, generative AI produces original output, which is why tools like ChatGPT and DALL-E feel so magical.",

    "What does it mean to fine-tune an AI model?":
        "Fine-tuning takes a model that already learned general knowledge from massive data and further trains it on a smaller, specific dataset. It's like a doctor who got a general medical degree and then specialized in cardiology.",

    "What is autonomous technology?":
        "Autonomous technology operates independently without direct human control — like self-driving cars, delivery drones, or robot vacuum cleaners. The AI makes its own decisions based on sensor data and programmed objectives.",

    "What year was the term 'artificial intelligence' first coined?":
        "The term was coined in 1956 at the Dartmouth Conference, organized by John McCarthy, Marvin Minsky, and others. This summer workshop is considered the founding event of AI as an academic field.",

    "What is predictive text?":
        "Predictive text is AI on your phone suggesting the next word you might type. It uses a small language model that learns from your texting habits and general language patterns to offer increasingly accurate suggestions.",

    "What is a smart speaker?":
        "A smart speaker is a speaker with a built-in AI voice assistant — like Amazon Echo (Alexa), Google Nest (Google Assistant), or Apple HomePod (Siri). You talk to it, and it plays music, answers questions, or controls your smart home.",

    "What is machine translation?":
        "Machine translation is using AI to automatically convert text or speech from one language to another. Modern systems use neural networks that understand context and grammar, producing translations that are far more natural than older word-by-word approaches.",

    "What is an AI-powered search engine?":
        "An AI-powered search engine uses language models and machine learning to understand the meaning behind your query, not just match keywords. Examples include Google's AI-enhanced search, Bing with Copilot, and Perplexity AI.",

    "What is the difference between hardware and software in AI?":
        "Hardware is the physical stuff — GPUs, CPUs, servers, and cables. Software is the AI program itself — the code and trained model. You need both: powerful hardware to run the software, and smart software to make the hardware useful.",

    "What is a robot vacuum an example of?":
        "A robot vacuum is a great example of narrow AI used in home automation. It uses sensors and simple AI algorithms to map your room, avoid obstacles, and efficiently clean floors — smart enough for one job, but it can't cook you dinner.",

    "Why might AI make mistakes?":
        "AI can only be as good as the data it trained on. If the training data was incomplete, biased, or incorrect, the AI will learn those flaws. It also can't reason about things it's never seen — it finds patterns, not truth.",

    "What is the Internet of Things (IoT)?":
        "IoT refers to the billions of everyday physical objects connected to the internet — smart fridges, fitness trackers, doorbell cameras, even smart toothbrushes. These devices collect data and often use AI to be more useful.",

    "What is an AI startup?":
        "An AI startup is a new company focused on building products or services powered by AI technology. The AI boom has created thousands of startups working on everything from medical diagnosis to creative writing to autonomous vehicles.",

    "What does 'open source' mean in AI?":
        "Open source means the AI's code and sometimes its model weights are shared publicly for anyone to use, modify, and build upon. Meta's Llama models are a famous example — anyone can download and run them for free.",

    "What is data privacy?":
        "Data privacy is your right to control how your personal information is collected, stored, and used. In AI, this is critical because models are trained on data that might include personal details, and AI systems can process your information at massive scale.",

    "What does AI-generated content mean?":
        "AI-generated content is any text, image, audio, video, or code created by an artificial intelligence system rather than a human. As AI gets better, telling AI-generated content from human-made content is becoming increasingly difficult.",

    "What is a virtual assistant?":
        "A virtual assistant is an AI program that helps you through conversation — answering questions, scheduling meetings, or managing tasks. Unlike a human assistant, it's available 24/7 and can handle multiple users simultaneously.",

    "What is the AI winter?":
        "AI winters were periods (roughly 1974-1980 and 1987-1993) when excitement about AI faded, funding dried up, and research stalled because early AI couldn't deliver on its grand promises. The current AI boom has been going strong since around 2012.",

    "What does 'training' an AI model require a lot of?":
        "Training requires massive computing power (thousands of GPUs running for weeks or months) and enormous datasets (billions of text samples, images, etc.). Training a large language model can cost millions of dollars in electricity alone.",

    "What is GitHub Copilot?":
        "GitHub Copilot is an AI coding assistant that suggests code as you type, like autocomplete on steroids. Built on OpenAI technology, it can write entire functions, explain code, and help developers work much faster.",

    "What does it mean for AI to be 'general purpose'?":
        "A general-purpose AI can handle many different types of tasks rather than just one. Modern LLMs are somewhat general-purpose — they can write code, answer questions, translate languages, and more — though they're still not truly 'general' AI.",

    "What is a language model?":
        "A language model is an AI system trained to predict and generate text by learning statistical patterns from enormous amounts of written language. It doesn't 'understand' language like you do — it's incredibly good at predicting what comes next.",

    "What is an AI chip?":
        "An AI chip is specialized hardware designed specifically for AI workloads — like NVIDIA's H100 GPU or Google's TPU. These chips are optimized for the matrix math that AI runs on, making them much faster and more efficient than general-purpose processors.",

    "What does 'training time' mean for an AI?":
        "Training time is how long it takes to teach an AI model by processing all the training data. For large language models, this can be weeks or months of non-stop computation on thousands of GPUs — it's a serious investment of time and electricity.",

    "What is a neural network's input layer?":
        "The input layer is the first layer of a neural network — it receives the raw data (like pixel values of an image or word tokens in a sentence). Each node in this layer represents one piece of input data that gets passed deeper into the network.",

    "What is a neural network's output layer?":
        "The output layer is the final layer that produces the model's answer — a classification label, a probability, or a predicted next word. The number of nodes in this layer matches the number of possible outputs the model can give.",

    "What is an API?":
        "An API (Application Programming Interface) is a set of rules that lets different software programs talk to each other. When an app uses AI, it usually sends your request to the AI through an API and gets the response back the same way.",

    "What is a dataset split?":
        "Data scientists split their data into three parts: training data (to teach the model), validation data (to tune settings during training), and test data (to evaluate final performance). This prevents the model from just memorizing answers.",

    "What is the difference between a rule-based system and machine learning?":
        "Rule-based systems follow explicit if-then rules that humans write (like 'if temperature > 100, then alarm'). Machine learning figures out the rules itself by studying examples. ML shines when the rules are too complex for humans to write.",

    "What is a chatbot's knowledge cutoff?":
        "A knowledge cutoff is the date after which an AI has no training data — it literally doesn't know about events that happened after that date. This is why chatbots sometimes give outdated answers about recent events.",

    "What is Google's AI chatbot called?":
        "Google's AI chatbot is called Gemini (formerly known as Bard). It's powered by Google's Gemini family of language models and can handle text, images, and code across Google's product ecosystem.",

    "What does 'real-time' mean in AI?":
        "Real-time means the AI processes input and delivers a response instantly — fast enough that there's no noticeable delay. Self-driving cars need real-time AI because a one-second delay at 60 mph means 88 feet of uncontrolled travel.",

    "What is an AI assistant's 'context'?":
        "Context is all the information available to the AI during your conversation — your previous messages, the system instructions, and any documents you've shared. More context helps the AI give more relevant and accurate responses.",

    "What is a spam filter an example of?":
        "A spam filter is a classic example of AI classification — it sorts each incoming email into one of two categories: spam or not spam. It learns from millions of examples of both to recognize the telltale signs of junk mail.",

    "What is Midjourney?":
        "Midjourney is an AI image generation tool that creates stunning artwork from text descriptions. It runs through Discord (a chat platform) and has become famous for its artistic, painterly style that many users find more aesthetically pleasing than competitors.",

    "What does 'iteration' mean when using AI?":
        "Iteration means refining your approach through multiple attempts. When working with AI, you often need to tweak your prompt, review the output, and try again — each round gets you closer to what you actually want.",

    "What is a large language model's main ability?":
        "At its core, an LLM is a next-token prediction machine — it predicts the most likely next word (or word piece) given everything that came before. This simple ability, scaled up massively, produces surprisingly intelligent-seeming behavior.",

    "What is an AI 'agent'?":
        "An AI agent is an AI system that can take actions, use tools, and make decisions to achieve goals — not just answer questions. It might browse the web, write code, manage files, or call other programs to complete a task autonomously.",

    "What is plagiarism in the context of AI?":
        "Using AI to write your essay and submitting it as your own work is a form of plagiarism. The key issue isn't using AI as a tool — it's claiming the work as entirely yours. Honesty about AI assistance matters.",

    "What does 'parameters' mean in an AI model?":
        "Parameters are the millions or billions of numerical values inside a model that get adjusted during training. They're the model's learned knowledge — like the synaptic strengths in a brain. GPT-4 is estimated to have over a trillion parameters.",

    "What is a benchmark in AI?":
        "A benchmark is a standardized test used to measure and compare how well AI models perform on specific tasks. Just like standardized tests for students, benchmarks let researchers objectively compare different AI systems.",

    "What does AI-powered mean?":
        "When a product is 'AI-powered,' it uses artificial intelligence under the hood to deliver smarter features. This could mean anything from a camera that enhances your photos to a search engine that understands natural questions.",

    "What is a robot arm in a factory an example of?":
        "A factory robot arm is an example of industrial automation — using machines (often guided by AI) to perform repetitive manufacturing tasks. These arms can weld, paint, assemble, and pack products faster and more consistently than humans.",

    "What is the main risk of relying too heavily on AI for information?":
        "The biggest risk is accepting incorrect information without question. AI can sound very authoritative even when it's wrong, so over-reliance can erode your critical thinking skills and lead you to make decisions based on false facts.",

    "What is the difference between strong AI and weak AI?":
        "Weak (narrow) AI does one thing well — like playing chess or translating text. Strong AI (AGI) would match human-level intelligence across all domains. Everything we have today is weak AI; strong AI remains a hypothetical future achievement.",

    "What is Watson?":
        "Watson is IBM's AI platform, famous for defeating two Jeopardy! champions on live TV in 2011. It processed natural language questions, searched its knowledge base, and buzzed in with answers — showing AI could handle open-ended trivia.",

    "What is a learning rate in AI?":
        "The learning rate controls how big of a step the model takes when adjusting its weights during training. Too high and it overshoots good solutions; too low and it learns painfully slowly. Finding the right balance is crucial.",

    "Can AI be creative?":
        "AI can generate novel, surprising outputs that feel creative — unusual images, inventive stories, fresh musical compositions. But this 'creativity' comes from recombining patterns in training data, not from imagination, emotions, or lived experience like human creativity.",

    "What is a training loop?":
        "A training loop is the repeated cycle of: feed data into the model, compare its output to the correct answer, calculate the error, and adjust the weights. This loop runs millions of times until the model gets good at its task.",

    "What is an epoch in machine learning?":
        "One epoch means the model has seen every single example in the training dataset once. Models typically train for many epochs — seeing the data multiple times — like re-reading a textbook to reinforce what you've learned.",

    "What is data cleaning?":
        "Data cleaning is the unglamorous but critical process of fixing messy data — removing duplicates, correcting errors, filling in missing values, and standardizing formats. Garbage in, garbage out: clean data is essential for good AI.",

    "What is object detection in AI?":
        "Object detection identifies what objects are in an image AND where they are, drawing bounding boxes around each one. Self-driving cars use it constantly to detect other vehicles, pedestrians, traffic signs, and lane markings.",

    "What is a prediction in machine learning?":
        "A prediction is the output a trained model produces when given new input — like predicting whether an email is spam, what the next word should be, or whether an X-ray shows a tumor. It's the model applying what it learned.",

    "What is feature extraction?":
        "Feature extraction is automatically pulling out the most useful patterns or attributes from raw data. Instead of humans deciding what matters (like 'count the number of edges'), the AI discovers which features are important on its own.",

    "What does 'accuracy' mean for an AI model?":
        "Accuracy is the simplest performance metric — the percentage of predictions the model got right out of all predictions. If it correctly classified 95 out of 100 images, it has 95% accuracy. But accuracy alone doesn't tell the whole story.",

    "What is a weight in a neural network?":
        "A weight is a number attached to each connection between neurons that determines how strongly one neuron influences another. During training, these weights are adjusted millions of times until the network produces accurate outputs.",

    "What is the output of an image classification model?":
        "An image classification model outputs a label or category — like 'cat,' 'dog,' or 'car' — along with a confidence score. It answers the question 'What is this a picture of?' rather than pointing to where things are in the image.",

    # =========================================================================
    # TIER 3 — Advanced Concepts (100 questions)
    # =========================================================================
    "What is deep learning?":
        "Deep learning is machine learning using neural networks with many layers (hence 'deep'). Each layer extracts increasingly abstract features — early layers might detect edges, middle layers detect shapes, and deep layers recognize entire objects.",

    "What happened at the Dartmouth Conference in 1956?":
        "The Dartmouth Conference was a summer workshop where John McCarthy, Marvin Minsky, and others formally proposed AI as a field of study and coined the term 'artificial intelligence.' It's considered the birthplace of AI research.",

    "Who is Geoffrey Hinton?":
        "Geoffrey Hinton is a British-Canadian computer scientist often called a 'Godfather of AI' for his pioneering work on neural networks and deep learning. He won the 2024 Nobel Prize in Physics for his contributions to machine learning foundations.",

    "What is a transformer in AI?":
        "The transformer is a neural network architecture introduced in 2017 that revolutionized AI. It uses 'attention' to process all parts of input simultaneously rather than sequentially, making it much faster and more powerful for language and other tasks.",

    "What does GPT stand for?":
        "GPT stands for Generative Pre-trained Transformer. 'Generative' means it creates text, 'Pre-trained' means it learned from massive data before being specialized, and 'Transformer' is the neural network architecture it's built on.",

    "What is the difference between supervised and unsupervised learning?":
        "Supervised learning trains on labeled examples (like photos tagged 'cat' or 'dog'), while unsupervised learning finds patterns in unlabeled data on its own. Think of it as learning with a teacher versus exploring and discovering patterns independently.",

    "What is reinforcement learning used for?":
        "Reinforcement learning trains AI through trial and error — rewarding good actions and penalizing bad ones. It's perfect for game-playing AI, robotics, and any situation where the AI needs to develop a strategy through experimentation.",

    "What is NLP?":
        "NLP stands for Natural Language Processing — the branch of AI that helps computers understand, interpret, and generate human language. It's behind chatbots, translation, voice assistants, sentiment analysis, and text summarization.",

    "Who is Yann LeCun?":
        "Yann LeCun is a French-American computer scientist who pioneered convolutional neural networks (CNNs) for image recognition and serves as Meta's Chief AI Scientist. Along with Hinton and Bengio, he's considered one of the 'Godfathers of AI.'",

    "What did IBM Deep Blue achieve in 1997?":
        "Deep Blue became the first computer system to defeat a reigning world chess champion (Garry Kasparov) in a full match under tournament conditions. It evaluated 200 million chess positions per second using specialized hardware.",

    "What is a convolutional neural network (CNN) best at?":
        "CNNs excel at processing images by using special filters that scan across the image to detect patterns like edges, textures, and shapes. They're the backbone of image recognition, medical imaging, and self-driving car vision systems.",

    "What are deepfakes most commonly used for?":
        "Unfortunately, deepfakes are most often used to create fake videos showing real people saying or doing things they never actually did. This poses serious threats to trust, politics, and personal reputation in our digital age.",

    "What is prompt engineering?":
        "Prompt engineering is the art and science of writing effective instructions for AI to get the best possible output. Small changes in wording can dramatically change results — it's a genuinely valuable skill in the age of AI.",

    "Who is Demis Hassabis?":
        "Demis Hassabis is a British AI researcher who co-founded DeepMind (now Google DeepMind). Under his leadership, DeepMind created AlphaGo, AlphaFold, and many other breakthroughs. He won the 2024 Nobel Prize in Chemistry for AlphaFold's protein structure predictions.",

    "What is transfer learning?":
        "Transfer learning means taking a model trained on one task (like recognizing general images) and adapting it for a different task (like identifying skin cancer). It saves enormous time and data because the model already knows useful features.",

    "What is overfitting in machine learning?":
        "Overfitting is when a model memorizes its training data so perfectly that it fails on new, unseen data. It's like a student who memorizes test answers word-for-word but can't solve problems phrased differently.",

    "What is the training-inference distinction?":
        "Training is the learning phase — processing massive data to adjust the model's weights over weeks or months. Inference is the using phase — applying the trained model to make predictions on new inputs, which takes milliseconds.",

    "What is a GAN?":
        "A GAN (Generative Adversarial Network) pits two neural networks against each other: a generator creates fake data, and a discriminator tries to spot the fakes. This competition drives both to improve, producing incredibly realistic outputs.",

    "Who is Fei-Fei Li?":
        "Fei-Fei Li is a computer scientist at Stanford who created ImageNet, a massive labeled image dataset that sparked the deep learning revolution. The annual ImageNet competition drove rapid advances in computer vision from 2010 to 2017.",

    "What is ImageNet?":
        "ImageNet is a dataset of over 14 million labeled images organized into thousands of categories. The ImageNet Large Scale Visual Recognition Challenge (starting 2010) became the proving ground where deep learning first showed its dominance.",

    "What is the attention mechanism in AI?":
        "Attention lets a model focus on the most relevant parts of input when processing each element. When translating 'the cat sat on the mat,' attention helps the model connect 'cat' with its verb 'sat' even if they're far apart.",

    "What is a recurrent neural network (RNN)?":
        "An RNN processes data sequentially, maintaining a 'memory' of previous inputs that influences how it handles each new one. This makes it natural for text and time-series data, though transformers have largely replaced RNNs for most tasks.",

    "What is the difference between AI and machine learning?":
        "AI is the broad goal of making machines that can think intelligently. Machine learning is a specific approach within AI where systems learn from data. All ML is AI, but not all AI is ML — some AI uses hand-coded rules instead.",

    "What is data augmentation?":
        "Data augmentation creates new training examples by modifying existing ones — flipping images, adding noise, changing brightness, or paraphrasing text. It's a clever way to make a small dataset act bigger, helping the model generalize better.",

    "What is AI alignment?":
        "AI alignment is the challenge of ensuring AI systems do what humans actually want, not just what they're technically told to do. A misaligned AI might find unexpected shortcuts that technically satisfy its objective while causing unintended harm.",

    "What is a loss function?":
        "A loss function measures how wrong the model's predictions are — the bigger the number, the worse the model is doing. Training is essentially the process of minimizing this loss function by adjusting the model's weights.",

    "What is edge AI?":
        "Edge AI means running AI directly on your device (phone, camera, car) instead of sending data to the cloud. It's faster (no internet lag), more private (data stays local), and works offline — your phone's face unlock is edge AI.",

    "What is synthetic data?":
        "Synthetic data is artificially generated data used to train AI when real data is too expensive, scarce, or privacy-sensitive to collect. AI can generate realistic fake medical records, for example, without risking any real patient's privacy.",

    "What is a feature in machine learning?":
        "A feature is one measurable property used as input — like a person's height, age, or income in a loan prediction model. Choosing the right features is crucial because they determine what information the model has to work with.",

    "How do self-driving cars perceive their surroundings?":
        "Self-driving cars combine multiple sensor types: cameras for visual detail, lidar for precise 3D mapping, radar for detecting speed and distance, and GPS for position. AI fuses all this data to build a real-time understanding of the road.",

    "What is few-shot learning?":
        "Few-shot learning means AI can perform a new task after seeing just a few examples — maybe 2 to 5. It's impressive because humans learn this way naturally, but most AI traditionally needed thousands of examples to learn anything.",

    "What is zero-shot learning?":
        "Zero-shot learning means AI can handle a task it was never specifically trained on, relying on general knowledge. For example, an LLM might correctly answer medical questions even though it wasn't specifically trained as a medical AI.",

    "What is model compression?":
        "Model compression shrinks a large AI model to run on smaller devices — your phone instead of a data center. Techniques include pruning (removing unnecessary connections), quantization (using less precise numbers), and distillation (training a smaller copy).",

    "What year did AlphaGo beat a world champion at Go?":
        "AlphaGo defeated world champion Lee Sedol 4 games to 1 in March 2016. Go was considered far harder for AI than chess because of its astronomical number of possible positions (more than atoms in the universe).",

    "What is batch processing in machine learning?":
        "Batch processing means the model processes multiple training examples simultaneously rather than one at a time. This is much more efficient because GPUs are designed for parallel computation — they can crunch a batch of 32 or 64 examples as fast as one.",

    "What is a pre-trained model?":
        "A pre-trained model has already been trained on a large general dataset, giving it broad knowledge that can be adapted for specific tasks. Using pre-trained models saves enormous time and cost — you don't have to teach AI everything from scratch.",

    "What is explainable AI (XAI)?":
        "Explainable AI develops methods for AI systems to show their reasoning in ways humans can understand. This matters for trust and accountability — a doctor needs to know why the AI flagged a scan as suspicious, not just that it did.",

    "What is the vanishing gradient problem?":
        "In deep networks, gradients (the signals used to update weights) can shrink to near-zero as they pass backward through many layers, making early layers unable to learn. This was a major obstacle until techniques like residual connections solved it.",

    "What is a knowledge graph?":
        "A knowledge graph is a structured database of facts and relationships — like 'Paris is-the-capital-of France' and 'France is-in Europe.' AI can traverse these graphs to answer complex questions by following chains of connected facts.",

    "What is word embedding?":
        "Word embedding converts words into numerical vectors (lists of numbers) where similar words have similar vectors. In embedding space, 'king' minus 'man' plus 'woman' actually equals something close to 'queen' — the math captures meaning!",

    "What ethical concern does facial recognition raise?":
        "Facial recognition raises serious privacy and surveillance concerns — governments or companies could track your movements everywhere without your knowledge. It also has accuracy problems with certain demographics, potentially leading to wrongful identifications.",

    "What is the role of a validation set in machine learning?":
        "The validation set is data held aside from training that's used to tune the model's settings (hyperparameters) and check for overfitting during training. It's like practice tests before the real exam (the test set).",

    "What is natural language generation?":
        "Natural language generation (NLG) is AI creating human-readable text from structured data or prompts. It's the technology behind chatbot responses, automated news articles, and AI writing assistants.",

    "What is a chatbot hallucination?":
        "A hallucination is when an AI chatbot confidently presents fabricated information as fact — citing fake studies, inventing quotes, or describing events that never happened. It happens because the model is predicting plausible-sounding text, not retrieving verified facts.",

    "What is AI governance?":
        "AI governance encompasses the policies, laws, standards, and oversight mechanisms for responsible AI development and deployment. It addresses who's accountable when AI causes harm, what transparency is required, and how to prevent misuse.",

    "What is the difference between classification and regression?":
        "Classification predicts which category something belongs to (spam or not spam, cat or dog), while regression predicts a continuous number (tomorrow's temperature, a house's price). Both are supervised learning, just with different types of outputs.",

    "What is a hyperparameter?":
        "A hyperparameter is a setting you choose before training starts — like the learning rate, number of layers, or batch size. Unlike regular parameters (which the model learns), hyperparameters are configured by the developer and stay fixed during training.",

    "What is the role of an activation function in a neural network?":
        "Activation functions introduce non-linearity into the network, which is essential for learning complex patterns. Without them, no matter how many layers you stack, the whole network would just be a simple linear equation.",

    "What is AI safety research?":
        "AI safety research focuses on making sure AI systems are reliable, predictable, and aligned with human values — especially as systems become more powerful. It's about preventing both obvious failures (crashes) and subtle ones (AI pursuing unintended goals).",

    "What company developed AlphaGo?":
        "AlphaGo was developed by DeepMind, a London-based AI lab founded in 2010 and acquired by Google in 2014. DeepMind is now called Google DeepMind and continues to be one of the world's leading AI research organizations.",

    "What is tokenization in NLP?":
        "Tokenization breaks text into smaller pieces (tokens) that the model can process. Modern LLMs use subword tokenization — splitting 'unhappiness' into 'un,' 'happiness' — which handles rare words efficiently while keeping common words intact.",

    "What is a confusion matrix?":
        "A confusion matrix is a table showing how many predictions fell into each category — true positives, false positives, true negatives, and false negatives. It reveals exactly where a model succeeds and where it gets confused.",

    "What is the role of dropout in neural networks?":
        "Dropout randomly deactivates a percentage of neurons during each training step, forcing the network to not rely too heavily on any single neuron. It's like a team where random members sit out each practice — everyone gets stronger.",

    "What is autonomous driving Level 5?":
        "Level 5 is the holy grail of self-driving: a car that can drive anywhere, in any conditions, without a human ever needing to take control. No Level 5 cars exist yet — even the most advanced systems today are Level 2-4.",

    "What problem do AI winters describe?":
        "AI winters describe boom-and-bust cycles where enormous hype about AI leads to overpromising, followed by disappointment when technology doesn't deliver, causing funding and interest to collapse. There were major AI winters in the 1970s and late 1980s.",

    "What is chain-of-thought prompting?":
        "Chain-of-thought prompting asks AI to 'think step by step' before giving a final answer. This dramatically improves performance on math and reasoning tasks because the model works through the logic rather than jumping to a conclusion.",

    "What is the purpose of a test set in machine learning?":
        "The test set is data the model never sees during training or tuning — it's the final exam. It gives an honest estimate of how well the model will perform on completely new, real-world data.",

    "What is a generative model?":
        "A generative model learns the underlying patterns in data well enough to create new, similar data. It can generate new faces, new text, or new music that looks and feels like the real thing but never existed before.",

    "What is Stable Diffusion?":
        "Stable Diffusion is an open-source AI image generation model released in 2022 by Stability AI. Because it's open source, anyone can download and run it on their own computer, which made high-quality AI image generation accessible to everyone.",

    "What is the main advantage of transformers over RNNs?":
        "Transformers can process all tokens in a sequence simultaneously using attention, while RNNs must process them one at a time in order. This parallelism makes transformers dramatically faster to train and better at capturing long-range relationships.",

    "What is responsible AI?":
        "Responsible AI means developing and deploying AI systems that are fair (no bias), transparent (explainable decisions), accountable (clear responsibility), and safe (no unintended harm). It's about building AI that works well for everyone, not just some.",

    "What is a recurrent neural network's hidden state?":
        "The hidden state is a vector (list of numbers) that acts as the RNN's memory, passed from one time step to the next. It captures a compressed summary of everything the network has seen so far in the sequence.",

    "What is LSTM?":
        "LSTM (Long Short-Term Memory) is a special type of RNN designed to remember information over long sequences. It uses 'gates' — forget, input, and output — to control what information to keep, update, or discard. It solved the vanishing gradient problem for sequential data.",

    "What is the bias-variance tradeoff?":
        "High bias means the model is too simple and misses patterns (underfitting). High variance means it memorizes noise and fails on new data (overfitting). The sweet spot is a model complex enough to capture real patterns but not so complex it memorizes noise.",

    "What is gradient clipping?":
        "Gradient clipping caps gradient values at a maximum threshold during training. Without it, gradients can 'explode' to enormous values in deep networks, causing wild weight updates that destroy what the model has learned.",

    "What is a generative adversarial network's discriminator?":
        "The discriminator is the 'art critic' in a GAN — it examines data and tries to determine whether it's real (from the training set) or fake (from the generator). As it gets better at spotting fakes, the generator is forced to create more realistic outputs.",

    "What is the purpose of a pooling layer in a CNN?":
        "Pooling shrinks feature maps by summarizing small regions (usually taking the maximum value). This reduces computation, prevents overfitting, and makes the model somewhat tolerant of slight shifts in where objects appear in the image.",

    "What is cross-validation?":
        "Cross-validation splits data into multiple folds, training on different combinations and averaging the results. This gives a much more reliable estimate of model performance than a single train-test split, especially with limited data.",

    "What is the F1 score?":
        "The F1 score is the harmonic mean of precision and recall, balancing both into a single number between 0 and 1. It's especially useful when classes are imbalanced — accuracy can be misleading, but F1 tells you if the model finds what matters.",

    "What is precision in machine learning classification?":
        "Precision answers: 'Of everything the model predicted as positive, how many were actually positive?' High precision means few false alarms. A spam filter with high precision rarely puts legitimate emails in your spam folder.",

    "What is recall in machine learning classification?":
        "Recall answers: 'Of all the actual positive cases, how many did the model find?' High recall means few missed cases. A cancer screening AI with high recall catches almost every tumor, even if it sometimes flags healthy tissue.",

    "What is a GAN's generator?":
        "The generator is the 'forger' in a GAN — it starts by producing random noise and gradually learns to create data so realistic that the discriminator can't tell it from real data. It never sees the real data directly; it only gets feedback from the discriminator.",

    "What is dimensionality reduction?":
        "Dimensionality reduction compresses data with many features into fewer dimensions while preserving the most important information. It's like summarizing a 10-page report into 1 page — you lose some detail but keep the essential message.",

    "What is the difference between online and offline learning?":
        "Offline (batch) learning trains on a fixed, complete dataset all at once. Online learning updates the model continuously as new data arrives, one example at a time. Online learning adapts to changing patterns but can be less stable.",

    "What is semantic search?":
        "Semantic search understands the meaning behind your query, not just the exact words. Searching 'how to fix a flat' returns tire repair results, not apartment renovation — because the AI understands context and intent.",

    "What is a decision tree?":
        "A decision tree is a model that makes predictions by asking a series of yes-or-no questions about the data, branching at each answer. It's one of the most interpretable ML models because you can follow the decision path like a flowchart.",

    "What is random forest?":
        "Random forest builds many decision trees, each trained on a random subset of the data, and combines their predictions by voting. This ensemble approach is much more accurate and robust than a single decision tree.",

    "What is clustering in unsupervised learning?":
        "Clustering groups similar data points together without being told what the groups should be. It's like sorting a bag of mixed candies by color and shape without anyone telling you the categories — the algorithm discovers natural groupings.",

    "What is the k-means algorithm?":
        "K-means divides data into k clusters by repeatedly assigning each point to its nearest cluster center and then updating those centers. You choose k (the number of clusters) and the algorithm finds the best arrangement automatically.",

    "What is anomaly detection?":
        "Anomaly detection spots unusual data points that don't fit the normal pattern — like a fraudulent credit card transaction, a failing machine part, or an unusual network access. It works by learning what 'normal' looks like and flagging anything that deviates.",

    "What is regularization?":
        "Regularization adds constraints during training to prevent the model from becoming overly complex and memorizing noise. Common methods include L1/L2 penalties (discouraging large weights) and dropout (randomly disabling neurons).",

    "What is an ensemble method?":
        "Ensemble methods combine multiple models' predictions to get a better result than any single model alone. It's the 'wisdom of crowds' principle — averaging many independent opinions usually beats any individual opinion.",

    "What does BERT stand for?":
        "BERT stands for Bidirectional Encoder Representations from Transformers. Created by Google in 2018, it was revolutionary because it reads text in both directions simultaneously, understanding context from both the left and right of each word.",

    "What makes BERT different from GPT?":
        "BERT reads text bidirectionally (both left-to-right and right-to-left), making it great for understanding text. GPT reads only left-to-right, making it great for generating text. BERT excels at comprehension tasks; GPT excels at creation tasks.",

    "What is curriculum learning?":
        "Curriculum learning trains a model on progressively harder examples, starting simple and increasing difficulty. Just like a student learning math — you start with addition before tackling calculus. This often leads to faster training and better final performance.",

    "What is an attention score?":
        "An attention score is a number indicating how relevant one token is to another when processing a sequence. High scores mean strong connection — in 'The cat sat on its mat,' 'its' would have a high attention score with 'cat.'",

    "What is the difference between generative and discriminative models?":
        "Generative models learn to create new data (like writing text or generating images). Discriminative models learn to classify or distinguish between categories (like identifying spam). One creates; the other categorizes.",

    "What is multi-task learning?":
        "Multi-task learning trains one model on several related tasks simultaneously, letting them share knowledge. A model learning translation, summarization, and question-answering together often performs better than three separate models.",

    "What is active learning?":
        "Active learning is a clever strategy where the model identifies which unlabeled examples it's most uncertain about and asks a human to label those specifically. This minimizes labeling effort by focusing on the most informative examples.",

    "What is a transformer's self-attention?":
        "Self-attention lets every token in a sequence look at every other token and decide which ones are most relevant. When processing 'The bank by the river,' self-attention helps 'bank' attend to 'river' to understand it means a riverbank, not a financial institution.",

    "What is the difference between AI ethics and AI safety?":
        "AI ethics addresses fairness, bias, privacy, and responsible use of current AI systems. AI safety focuses on preventing AI from causing harm, especially as systems become more powerful — including catastrophic risks from future advanced AI.",

    "What is data poisoning?":
        "Data poisoning is a deliberate attack where someone injects corrupted or misleading data into a training set to make the model behave incorrectly. It's like a saboteur slipping wrong answers into a textbook to make students learn the wrong things.",

    "What is adversarial robustness?":
        "Adversarial robustness measures how well a model maintains correct predictions when given inputs specifically designed to trick it. A tiny, invisible change to an image of a panda could make an AI classify it as a gibbon — robust models resist this.",

    "What is federated learning?":
        "Federated learning trains AI across many devices (like phones) without the data ever leaving those devices. Each phone trains a local model and shares only the learned updates, not the raw data — preserving privacy while still improving the AI.",

    "What is the softmax temperature relationship?":
        "Temperature scales the logits (raw scores) before softmax converts them to probabilities. High temperature (like 2.0) makes all options more equally likely (more random/creative); low temperature (like 0.1) concentrates probability on the top choice (more focused/deterministic).",

    "What is an adversarial example?":
        "An adversarial example is an input with carefully crafted tiny modifications that fool an AI model. Adding imperceptible noise to an image of a stop sign could make a self-driving car's AI see it as a speed limit sign — a dangerous vulnerability.",

    "What is a support vector machine (SVM)?":
        "An SVM finds the best boundary (hyperplane) that separates different classes of data with the maximum margin. Imagine drawing the widest possible road between two groups of points — the SVM finds exactly that optimal dividing line.",

    "What is the cosine similarity metric?":
        "Cosine similarity measures how similar two vectors are by calculating the cosine of the angle between them. A value of 1 means identical direction (very similar), 0 means unrelated, and -1 means opposite. It's widely used to compare word embeddings.",

    "What is a reward signal in reinforcement learning?":
        "A reward signal is numerical feedback telling the AI how good or bad its latest action was. A positive reward says 'do more of that,' a negative one says 'avoid that.' The AI learns to maximize total reward over time.",

    "What is the explore-exploit tradeoff?":
        "Should the AI try something new (explore) or stick with what's already working (exploit)? Too much exploration wastes time on bad options; too much exploitation misses better strategies. Finding the right balance is a fundamental challenge in reinforcement learning.",

    # =========================================================================
    # TIER 4 — Technical (91 questions)
    # =========================================================================
    "What is the attention mechanism in the transformer architecture?":
        "Transformer attention computes a relevance score between every pair of tokens using query, key, and value matrices. Each token 'asks a question' (query), other tokens offer 'answers' (keys), and the final output blends values weighted by relevance — enabling rich contextual understanding.",

    "What is backpropagation?":
        "Backpropagation calculates how much each weight contributed to the model's error by working backward from the output layer to the input layer using the chain rule of calculus. It's the engine that makes neural network training possible.",

    "What is gradient descent?":
        "Gradient descent is like walking downhill in a foggy mountain — you feel which direction slopes down (the gradient) and take a step that way. Each step adjusts the model's weights to reduce error, gradually finding the best configuration.",

    "What is a token in the context of large language models?":
        "A token is a chunk of text that the model processes as one unit — it might be a full word ('hello'), a subword ('un' + 'happy'), or even a single character. GPT-4 uses roughly 1 token per 0.75 English words.",

    "What is an embedding in AI?":
        "An embedding maps discrete items (words, images, users) into dense numerical vectors in a continuous space where similarity is measured by distance. It's how AI converts things it can't do math on (words) into things it can (numbers).",

    "What is a context window?":
        "The context window is the maximum number of tokens a language model can 'see' at once — its working memory. Early GPT models had 2K tokens; modern models like Claude can handle 200K+ tokens, enabling analysis of entire books.",

    "What is RLHF?":
        "RLHF (Reinforcement Learning from Human Feedback) is a training technique where humans rank AI outputs by quality, a reward model learns these preferences, and then the AI is optimized to produce responses humans prefer. It's how chatbots become helpful and safe.",

    "What is a diffusion model?":
        "A diffusion model learns to generate images by first adding noise to training images until they're pure static, then learning to reverse the process — removing noise step by step to create clear images. DALL-E 3, Stable Diffusion, and Midjourney all use this approach.",

    "When was ChatGPT released?":
        "ChatGPT launched on November 30, 2022, and reached 100 million users within two months — making it the fastest-growing consumer app in history at the time. It brought large language models into mainstream public awareness.",

    "What is Constitutional AI?":
        "Constitutional AI (CAI) is Anthropic's training approach where the AI is given a set of principles (a 'constitution') and learns to self-critique and revise its own outputs to be more helpful, harmless, and honest — reducing reliance on human feedback.",

    "What is the alignment problem?":
        "The alignment problem is the challenge of making sure powerful AI systems actually pursue the goals humans intend, not unintended interpretations. An AI told to 'minimize patient suffering' shouldn't conclude that eliminating patients solves the problem.",

    "What is the difference between training and inference in AI?":
        "Training is the expensive learning phase (weeks on thousands of GPUs), while inference is the fast application phase (milliseconds on one GPU). A model is trained once but performs inference millions of times serving users.",

    "What is fine-tuning in the context of large language models?":
        "Fine-tuning takes a pre-trained LLM and further trains it on a specific, smaller dataset — like medical texts, legal documents, or customer service conversations. The model keeps its general knowledge while becoming an expert in the target domain.",

    "What are scaling laws in AI?":
        "Scaling laws show that model performance improves predictably as you increase model size, training data, and compute. Discovered by researchers at OpenAI, these laws help predict how good a model will be before spending millions training it.",

    "What is the role of a reward model in RLHF?":
        "The reward model is trained on human preference data to score any AI output by quality. During RLHF training, it acts as a stand-in for human judgment, providing instant feedback to the language model on millions of outputs that would be impossible for humans to rate.",

    "What is a GPU's advantage over a CPU for AI training?":
        "A CPU has a few powerful cores optimized for sequential tasks, while a GPU has thousands of smaller cores for massive parallelism. AI training is mostly matrix multiplication — a naturally parallel task — which is why GPUs are 10-100x faster for it.",

    "What is multi-head attention?":
        "Multi-head attention runs several attention mechanisms in parallel, each with different learned weights. Each 'head' can focus on different types of relationships — one might track grammar, another might track meaning, another might track position.",

    "What is the softmax function used for in neural networks?":
        "Softmax converts a vector of raw scores (logits) into a probability distribution where all values are between 0 and 1 and sum to 1. It turns 'this option scored 5, that scored 3' into 'this has 88% probability, that has 12%.'",

    "What year was GPT-3 released?":
        "GPT-3 was released by OpenAI in June 2020 with 175 billion parameters — a massive leap from GPT-2's 1.5 billion. It demonstrated that scaling up language models dramatically improved their ability to write, reason, and code.",

    "What is a positional encoding in transformers?":
        "Since transformers process all tokens simultaneously (not sequentially), they need positional encodings to know word order. These encodings add information about each token's position in the sequence — otherwise 'dog bites man' and 'man bites dog' would look identical.",

    "What is the feed-forward network in a transformer block?":
        "After the attention layer determines which tokens are relevant to each other, the feed-forward network processes each token's representation independently through two linear transformations with an activation function. It's where much of the model's factual knowledge is stored.",

    "What is layer normalization?":
        "Layer normalization standardizes the values flowing through each layer so they have a consistent mean and variance. This stabilizes training by preventing values from growing too large or too small, letting deeper networks train reliably.",

    "What is the temperature parameter in language model generation?":
        "Temperature controls how random or focused the model's word choices are. At temperature 0, it always picks the most likely word (deterministic). At high temperature, it gives more chance to less likely words (creative but potentially chaotic).",

    "What is top-k sampling?":
        "Top-k sampling restricts the model's next-word choices to only the k highest-probability options, then randomly selects from those. With k=10, the model picks from its top 10 candidates, filtering out low-probability nonsense while keeping some variety.",

    "What is top-p (nucleus) sampling?":
        "Top-p (nucleus) sampling keeps the smallest set of tokens whose combined probability exceeds p (like 0.9). Unlike top-k which uses a fixed number, top-p adapts — using fewer options when the model is confident and more when it's uncertain.",

    "What is model distillation?":
        "Model distillation trains a smaller 'student' model to mimic a larger 'teacher' model's outputs, including its confidence levels. The student learns richer information than it would from raw data alone, achieving surprisingly close performance at a fraction of the size.",

    "What is LoRA (Low-Rank Adaptation)?":
        "LoRA fine-tunes a model by adding small trainable matrices alongside the frozen original weights. Instead of updating billions of parameters, you train only millions of new ones — making fine-tuning 10-100x cheaper while achieving nearly the same quality.",

    "What is quantization in AI models?":
        "Quantization reduces the precision of model weights — for example, from 32-bit to 8-bit or even 4-bit numbers. This dramatically shrinks the model's memory footprint and speeds up inference, with surprisingly little loss in quality.",

    "What is the purpose of residual connections in transformers?":
        "Residual (skip) connections add the input of each layer directly to its output, creating a shortcut. This lets gradients flow freely backward through the network during training, solving the vanishing gradient problem and enabling very deep models.",

    "What is PPO in the context of RLHF?":
        "PPO (Proximal Policy Optimization) is the reinforcement learning algorithm commonly used in RLHF to update the language model. It makes small, stable updates to the model's behavior, preventing it from changing too drastically in any single training step.",

    "What is the cross-entropy loss function?":
        "Cross-entropy measures how different the model's predicted probability distribution is from the true answer. For language models, it asks: 'How surprised was the model by the correct next word?' Lower cross-entropy means better predictions.",

    "What is a vision transformer (ViT)?":
        "A Vision Transformer splits an image into small patches (like 16x16 pixels), treats each patch as a 'token,' and processes them with a standard transformer. This showed that transformers — originally designed for text — work brilliantly for images too.",

    "What is the key innovation of the original transformer paper?":
        "The 2017 'Attention Is All You Need' paper showed that you could build a powerful sequence model using only attention mechanisms, completely eliminating the recurrence (sequential processing) that RNNs required. This unlocked massive parallelization during training.",

    "What is AlphaFold?":
        "AlphaFold is DeepMind's AI that predicts the 3D structure of proteins from their amino acid sequence — a problem biologists struggled with for 50 years. It predicted structures for nearly all known proteins, revolutionizing biology and earning a Nobel Prize.",

    "What is an AI safety benchmark?":
        "AI safety benchmarks are standardized tests that evaluate whether models behave safely — checking for toxicity, bias, truthfulness, and resistance to manipulation. They're the 'crash tests' of the AI world, helping developers find and fix dangerous behaviors.",

    "What is self-supervised learning?":
        "Self-supervised learning creates its own labels from the data — like hiding words in a sentence and asking the model to predict them. It's how GPT learns (predicting next words) and how BERT learns (predicting masked words), enabling training on unlimited unlabeled text.",

    "What is catastrophic forgetting?":
        "Catastrophic forgetting happens when training a neural network on new data causes it to lose what it learned before — like studying French so hard you forget all your Spanish. Techniques like EWC and progressive networks help mitigate this.",

    "What does FLOPS stand for in AI computing?":
        "FLOPS stands for Floating-Point Operations Per Second — the standard measure of computing speed. Training GPT-4 reportedly required around 10^25 FLOPS total, which is why massive GPU clusters are needed.",

    "What is the encoder-decoder architecture?":
        "The encoder compresses the input into a rich internal representation, and the decoder generates the output from that representation. It's the architecture behind machine translation — the encoder understands French, the decoder produces English.",

    "What is beam search in text generation?":
        "Beam search explores multiple promising word sequences simultaneously, keeping the top-n candidates (the 'beam width') at each step. It finds better overall sequences than greedy search (which just picks the best word at each step) by looking ahead.",

    "What is contrastive learning?":
        "Contrastive learning teaches models to pull similar items closer together and push dissimilar items apart in embedding space. It learns by comparing pairs: 'these two images are of the same cat' versus 'this cat and this car are different.'",

    "What is an autoencoder?":
        "An autoencoder compresses data into a small representation (encoding) and then reconstructs the original from that compression (decoding). It's forced to learn the most essential features because it must rebuild the input from a bottleneck.",

    "What is the purpose of the key, query, and value matrices in attention?":
        "Queries represent 'what am I looking for?', keys represent 'what do I contain?', and values represent 'what information do I provide?' The dot product of queries and keys determines attention weights, which are used to create a weighted combination of values.",

    "What is mixed precision training?":
        "Mixed precision uses 16-bit floats for most computations (faster, less memory) while keeping 32-bit precision for critical operations (accuracy). This typically doubles training speed and halves memory usage with negligible quality loss.",

    "What is a variational autoencoder (VAE)?":
        "A VAE learns to encode data into a smooth, continuous probability distribution (latent space) rather than fixed points. This lets you sample new points from that space to generate new data — interpolating smoothly between, say, a smiling face and a frowning one.",

    "What is CLIP?":
        "CLIP (Contrastive Language-Image Pre-training) by OpenAI learns to connect images and text in a shared embedding space. It can classify images using any text description without specific training, enabling zero-shot visual understanding.",

    "What is instruction tuning?":
        "Instruction tuning fine-tunes a language model on examples of following human instructions — 'summarize this article,' 'translate to French,' 'write a poem about cats.' This transforms a raw text predictor into a helpful assistant that does what you ask.",

    "What is a latent space?":
        "A latent space is a compressed, abstract representation learned by a model where each point corresponds to a possible output. Similar items cluster nearby — in an image model's latent space, all cat images occupy a similar region, smoothly transitioning to dog images.",

    "What is weight decay in training?":
        "Weight decay is a regularization technique that slightly shrinks all weights toward zero at each training step. This penalizes overly complex models with large weights, encouraging simpler solutions that generalize better to new data.",

    "What is the Adam optimizer?":
        "Adam combines two powerful ideas: momentum (remembering past gradient directions) and adaptive learning rates (adjusting step size per parameter based on gradient history). It's the most popular optimizer in deep learning because it works well with minimal tuning.",

    "What is sparse attention?":
        "Sparse attention only computes attention between selected token pairs instead of all pairs, reducing the quadratic cost. Patterns include local attention (nearby tokens), strided attention (every nth token), or learned patterns — enabling much longer sequences.",

    "What is data parallelism in distributed training?":
        "Data parallelism puts a complete copy of the model on each GPU but splits the training data across them. Each GPU processes its chunk, computes gradients, and they synchronize before updating — like having multiple students read different chapters and sharing notes.",

    "What is a system prompt?":
        "A system prompt is a set of instructions given to an AI model before the conversation begins, defining its personality, rules, and boundaries. It's how developers configure the AI to be a coding assistant, a creative writer, or a customer service agent.",

    "What is the difference between autoregressive and masked language models?":
        "Autoregressive models (GPT) predict the next token using only previous tokens — great for generation. Masked models (BERT) predict hidden tokens using surrounding context from both sides — great for understanding. Different training, different strengths.",

    "What is model parallelism?":
        "Model parallelism splits a single model across multiple GPUs when the model is too large to fit on one. Different layers or components run on different GPUs, with data passing between them — essential for training the largest language models.",

    "What is a foundation model?":
        "A foundation model is a large AI model trained on broad data that serves as the base for many different applications. GPT-4, Claude, and Llama are foundation models — they can be adapted for writing, coding, analysis, and countless other tasks.",

    "What is tensor parallelism?":
        "Tensor parallelism splits individual matrix multiplications across multiple GPUs by dividing the weight matrices. Each GPU computes part of the result, and they combine outputs. It's essential for layers too large for a single GPU's memory.",

    "What is pipeline parallelism?":
        "Pipeline parallelism assigns different layers of a model to different GPUs in sequence, like an assembly line. While GPU-1 processes the next batch's early layers, GPU-2 is already working on the current batch's later layers.",

    "What is the Chinchilla paper's formal name?":
        "The paper is titled 'Training Compute-Optimal Large Language Models' by Hoffmann et al. at DeepMind (2022). It showed that most large models were over-sized and under-trained, proposing that data and parameters should scale equally for optimal performance.",

    "What is a mixture of experts' gating network?":
        "The gating network (router) is a small neural network that examines each input token and decides which expert subnetworks to activate. Typically only 2 out of perhaps 64 experts are activated per token, making the model efficient despite its massive total size.",

    "What is the difference between batch normalization and layer normalization?":
        "Batch norm normalizes across different examples in a batch (computing stats per feature across the batch), while layer norm normalizes across all features within a single example. Transformers use layer norm because it works regardless of batch size.",

    "What is BPE (Byte Pair Encoding)?":
        "BPE starts with individual characters and iteratively merges the most frequently co-occurring pairs into single tokens. 'th' + 'e' becomes 'the,' common words stay whole, and rare words get split into recognizable pieces — an elegant balance.",

    "What is the perplexity metric?":
        "Perplexity measures how 'surprised' a language model is by text — lower perplexity means the model predicted the words well. A perplexity of 10 means the model was, on average, as uncertain as if choosing between 10 equally likely options.",

    "What is nucleus sampling another name for?":
        "Nucleus sampling is another name for top-p sampling. 'Nucleus' refers to the core group of tokens whose cumulative probability forms the 'nucleus' of the distribution. The 2020 paper that introduced it used this term because you're sampling from the probability mass's core.",

    "What is gradient accumulation?":
        "Gradient accumulation processes several small batches and sums their gradients before updating weights, simulating a larger batch size. This lets you effectively train with batch sizes that wouldn't fit in GPU memory all at once.",

    "What is the purpose of warmup in learning rate scheduling?":
        "Warmup starts training with a very low learning rate and gradually increases it over the first few hundred or thousand steps. This prevents the randomly initialized model from taking destructive large steps early on when gradients are unreliable.",

    "What is knowledge distillation's teacher-student framework?":
        "A large, accurate 'teacher' model generates soft predictions (probability distributions, not just labels) that a smaller 'student' model learns to mimic. The soft targets contain richer information than hard labels, teaching the student nuanced patterns.",

    "What is the BLEU score used for?":
        "BLEU (Bilingual Evaluation Understudy) measures machine translation quality by comparing the model's output against human reference translations. It counts matching word sequences (n-grams), giving a score from 0 to 1 where higher is better.",

    "What is causal masking in transformers?":
        "Causal masking blocks each token from seeing any future tokens in the sequence during self-attention. This ensures the model only uses past context when predicting the next word, which is essential for autoregressive text generation.",

    "What is the difference between pre-training and fine-tuning?":
        "Pre-training is the massive initial phase where the model learns general knowledge from huge datasets (the expensive part). Fine-tuning is the targeted follow-up where you adapt the pre-trained model to a specific task with a smaller dataset (the cheap part).",

    "What is SwiGLU?":
        "SwiGLU combines the Swish activation function with a Gated Linear Unit, creating a more expressive feed-forward layer. It's used in models like LLaMA and PaLM because it consistently outperforms simpler activation functions like ReLU at the same parameter count.",

    "What is RMSNorm?":
        "RMSNorm (Root Mean Square Normalization) normalizes using only the RMS of activations, skipping the mean-subtraction step of layer norm. It's simpler, slightly faster, and works just as well — which is why modern LLMs like LLaMA prefer it.",

    "What is group query attention (GQA)?":
        "GQA is a compromise between multi-head attention (separate KV per head, expensive) and multi-query attention (shared KV for all heads, cheap but lower quality). It groups heads into clusters that share key-value heads, balancing quality and efficiency.",

    "What is the chinchilla scaling prediction for a 70B parameter model?":
        "The Chinchilla paper found that model size and training data should scale equally — roughly 20 tokens per parameter. So a 70B parameter model needs about 1.4 trillion training tokens to be compute-optimal.",

    "What is DDP in distributed training?":
        "DDP (Distributed Data Parallel) places a complete model copy on each GPU, splits the training batch across them, and synchronizes gradients after each step. It's PyTorch's primary tool for multi-GPU training and scales almost linearly.",

    "What is the purpose of a tokenizer in LLMs?":
        "The tokenizer is the translator between human text and numbers the model understands. It splits text into tokens and maps each to a unique integer ID. The same tokenizer must be used for both training and inference to maintain consistency.",

    "What is ZeRO (Zero Redundancy Optimizer)?":
        "ZeRO eliminates memory redundancy in data parallelism by partitioning optimizer states, gradients, and parameters across GPUs instead of duplicating them. ZeRO-3 (the most aggressive stage) lets each GPU store only a fraction of the full model.",

    "What is the difference between RLHF and DPO?":
        "RLHF trains a separate reward model from human preferences and then uses reinforcement learning to optimize against it — a two-step process. DPO skips the reward model entirely, directly optimizing the language model on preference pairs. DPO is simpler and often just as effective.",

    "What is the 'next token prediction' objective?":
        "Next token prediction trains the model to predict what comes next given everything before it. Despite its simplicity, this objective — scaled to billions of parameters and trillions of tokens — produces remarkably capable models that can reason, code, and converse.",

    "What is the role of the optimizer in training?":
        "The optimizer takes the gradients computed by backpropagation and decides exactly how to update each weight. Different optimizers (SGD, Adam, AdaFactor) use different strategies — some track momentum, some adapt learning rates per parameter.",

    "What is a cosine learning rate schedule?":
        "A cosine schedule decreases the learning rate following a smooth cosine curve from a peak value down to near zero. This gradual cooldown lets the model make large improvements early in training and fine-grained adjustments later.",

    "What does 'inference latency' mean?":
        "Inference latency is the time between sending a request to an AI model and receiving the response. For chatbots it's how long you wait for a reply; for self-driving cars it's the critical reaction time measured in milliseconds.",

    "What is the attention complexity of standard self-attention?":
        "Standard self-attention has O(n^2) complexity because every token attends to every other token — doubling the sequence length quadruples the computation. This is why long context windows are so expensive and why efficient attention methods are important.",

    "What is a safety filter in AI systems?":
        "A safety filter screens model outputs before they reach the user, blocking content that's harmful, toxic, or violates policies. It's one layer of defense — working alongside training-time safety techniques like RLHF and Constitutional AI.",

    "What is FSDP (Fully Sharded Data Parallel)?":
        "FSDP shards all model components (parameters, gradients, optimizer states) across GPUs, gathering them on-the-fly only when needed for computation. It enables training models much larger than a single GPU's memory while maintaining efficient throughput.",

    "What is the role of a classifier-free guidance in diffusion models?":
        "Classifier-free guidance generates both a conditional output (following the prompt) and an unconditional output (no prompt), then amplifies the difference. Higher guidance strength makes the image follow the prompt more closely at the cost of some diversity.",

    "What is the 'curse of dimensionality'?":
        "As the number of features (dimensions) increases, data becomes increasingly sparse — the volume of the space grows exponentially while the data stays the same size. Models need exponentially more data to maintain the same density of examples.",

    "What is a Mixture of Experts model's key efficiency advantage?":
        "Despite having enormous total parameter counts, MoE models only activate a small fraction of parameters for each input token. A 1.8 trillion parameter MoE might only use 280 billion per token, getting the benefits of scale with a fraction of the compute.",

    "What is the sigmoid function?":
        "The sigmoid function squashes any input value into a smooth S-curve between 0 and 1, making it perfect for representing probabilities. It was the original neural network activation function, though ReLU has largely replaced it in hidden layers.",

    "What is ReLU?":
        "ReLU (Rectified Linear Unit) is the simplest popular activation function: it outputs the input if positive, or zero if negative. Its simplicity and efficiency solved the vanishing gradient problem and made deep network training practical.",

    "What is the cross-attention mechanism?":
        "Cross-attention lets one sequence attend to a different sequence — for example, a decoder attending to encoder outputs during translation. The queries come from the decoder (what it's generating) while keys and values come from the encoder (the source text).",

    # =========================================================================
    # TIER 5 — Expert/Research (80 questions)
    # =========================================================================
    "What is the title of the 2017 paper that introduced the transformer?":
        "The groundbreaking paper is titled 'Attention Is All You Need' by Vaswani et al. at Google. Its bold title reflected its bold claim: attention mechanisms alone, without recurrence or convolution, could outperform all existing sequence models.",

    "Who were the authors of 'Attention Is All You Need'?":
        "The paper was authored by Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan Gomez, Lukasz Kaiser, and Illia Polosukhin. Several went on to found major AI companies, including Cohere and Character.AI.",

    "What are Chinchilla optimal scaling laws?":
        "Chinchilla (Hoffmann et al., 2022) showed that prior models like GPT-3 were too large for their training data. The optimal balance is roughly equal scaling of parameters and training tokens — meaning a 70B model needs about 1.4 trillion tokens.",

    "What is mechanistic interpretability?":
        "Mechanistic interpretability reverse-engineers neural networks to understand exactly how they compute internally — identifying specific circuits, features, and algorithms. It's like opening the hood of a car to understand each component, not just measuring speed.",

    "What is the EU AI Act?":
        "The EU AI Act (passed 2024) is the world's first comprehensive AI law. It classifies AI systems by risk level — banning some (like social scoring), heavily regulating high-risk ones (medical, law enforcement), and lightly regulating low-risk ones.",

    "What are emergent capabilities in large language models?":
        "Emergent capabilities are abilities that suddenly appear when models reach a certain scale but are absent in smaller models. For example, GPT-3 could do few-shot arithmetic that GPT-2 could not — the capability emerged from scale alone.",

    "What is in-context learning?":
        "In-context learning means the model learns to perform a task just from examples provided in the prompt — without any weight updates. You show it a few examples of translating English to French, and it figures out the pattern on the fly.",

    "What is a mixture of experts (MoE) architecture?":
        "MoE models contain many specialized subnetworks (experts) and a router that selects which experts to activate for each input. This allows massive total parameter counts while keeping per-token compute manageable — it's how models can be both huge and efficient.",

    "What is instrumental convergence?":
        "Instrumental convergence is the idea that AIs with very different ultimate goals would still pursue common subgoals — like self-preservation, resource acquisition, and maintaining their current objectives. A paperclip maximizer and a cure-cancer AI both benefit from not being shut down.",

    "What is mesa-optimization?":
        "Mesa-optimization occurs when a trained model develops its own internal optimizer with its own objective (the 'mesa-objective') that may differ from the training objective. The outer training loop creates an inner optimizer it doesn't fully control.",

    "What is the Kaplan scaling laws paper about?":
        "Kaplan et al. (2020) at OpenAI discovered that language model performance follows smooth power laws as you increase model size, dataset size, and compute. These predictable relationships let researchers forecast model capabilities before expensive training runs.",

    "What is DPO (Direct Preference Optimization)?":
        "DPO reformulates RLHF as a simple classification problem — directly training the model to prefer outputs humans ranked higher, without needing a separate reward model or RL algorithm. It's mathematically equivalent to RLHF but much simpler to implement.",

    "What is the concept of superposition in neural networks?":
        "Superposition is when a neural network represents more features than it has dimensions by overlapping them in shared neurons. It's like writing multiple messages on the same page in different colored inks — efficient but hard to disentangle.",

    "What is a circuit in the context of mechanistic interpretability?":
        "A circuit is a specific subnetwork within a neural network that performs an identifiable computation — like an 'indirect object identification circuit' that tracks who did what to whom. Mapping these circuits is like finding the wiring diagram for intelligent behavior.",

    "What is Constitutional AI's core innovation?":
        "CAI's key insight is using AI to supervise AI — the model critiques and revises its own outputs according to a written set of principles. This dramatically reduces the need for expensive human feedback while producing safer, more helpful behavior.",

    "What is the 'lottery ticket hypothesis'?":
        "Frankle and Carlin (2018) showed that dense neural networks contain small sparse subnetworks ('winning tickets') that, when trained in isolation from scratch, can match the full network's performance. Most of the network's parameters are essentially redundant.",

    "What is KV-cache in transformer inference?":
        "During text generation, the model computes key and value tensors for each token. The KV-cache stores these so they don't need to be recomputed when generating each new token. Without it, generation time would grow quadratically with sequence length.",

    "What is rotary positional encoding (RoPE)?":
        "RoPE encodes position by rotating the query and key vectors in pairs of dimensions. The clever part: the dot product between rotated queries and keys depends only on their relative position, not absolute — giving transformers better generalization to unseen sequence lengths.",

    "What is the difference between decoder-only and encoder-decoder transformers?":
        "Decoder-only models (GPT, Claude) generate text token by token using causal masking. Encoder-decoder models (T5, original transformer) first encode the full input bidirectionally, then decode the output. Decoder-only has become dominant for general language models.",

    "What is Anthropic's approach to AI safety called?":
        "Anthropic's approach is called Constitutional AI (CAI). It defines a set of principles (the 'constitution') that the AI uses to self-critique and improve its responses, creating a scalable alternative to pure human feedback for alignment.",

    "What is speculative decoding?":
        "Speculative decoding uses a small, fast 'draft' model to quickly generate several candidate tokens, then the large model verifies them all at once in a single forward pass. Accepted tokens are kept, rejected ones are re-generated — dramatically speeding up inference.",

    "What is the 'Bitter Lesson' by Rich Sutton?":
        "Rich Sutton's 2019 essay argues that the biggest lesson from 70 years of AI research is that general methods that scale with computation always eventually beat clever human-designed approaches. Brute force plus scale wins in the long run.",

    "What is flash attention?":
        "Flash Attention by Tri Dao (2022) is an IO-aware implementation of exact attention that minimizes reads/writes to GPU memory. It computes attention in tiles, keeping data in fast SRAM instead of slow HBM, achieving 2-4x speedup with no approximation.",

    "What is the Chinchilla model's key finding about optimal training?":
        "Chinchilla showed that for any fixed compute budget, you should spend roughly equal resources on model size and training data — about 20 tokens per parameter. This meant models like GPT-3 were over-parameterized and under-trained for their compute budget.",

    "What is activation patching in interpretability?":
        "Activation patching replaces a model's internal activations at a specific layer/position with activations from a different input, then observes how the output changes. This isolates which components are responsible for specific behaviors — surgical debugging for neural networks.",

    "What is the 'grokking' phenomenon?":
        "Grokking (Power et al., 2022) showed that models can suddenly generalize long after apparently memorizing the training data. A model might achieve 100% training accuracy at step 1000 but not generalize until step 100,000 — the understanding suddenly 'clicks.'",

    "What is a reward hacking in reinforcement learning?":
        "Reward hacking is when an AI finds a loophole to maximize its reward score without actually doing what was intended. A cleaning robot might learn to hide mess under the rug (high 'clean floor' score) instead of actually cleaning — satisfying the letter but not the spirit.",

    "What are induction heads in transformers?":
        "Induction heads are a specific two-head circuit that implements in-context pattern copying. One head identifies 'I've seen token A followed by token B before,' and the other uses that to predict B when A appears again — a fundamental building block of in-context learning.",

    "What is the 'alignment tax'?":
        "The alignment tax is the performance cost of making AI safer. If RLHF makes a model slightly less capable at coding in order to refuse harmful requests, that capability reduction is the alignment tax. The goal is to minimize this tax while maximizing safety.",

    "What is Goodhart's Law as applied to AI?":
        "Goodhart's Law says 'when a measure becomes a target, it ceases to be a good measure.' In AI, if you optimize a reward model too aggressively, the AI learns to exploit the reward signal rather than actually being helpful — producing outputs that score well but are low quality.",

    "What is multi-modal AI?":
        "Multi-modal AI can process and relate different types of data simultaneously — text, images, audio, video. GPT-4V can look at an image and discuss it in text; Gemini can understand video. This mirrors human intelligence, which naturally integrates multiple senses.",

    "What is the difference between GPT and BERT architectures?":
        "GPT uses a decoder-only transformer that predicts the next token left-to-right, while BERT uses an encoder-only transformer that predicts masked tokens bidirectionally. GPT excels at generating text while BERT excels at understanding it — both are transformers, just trained very differently.",

    "What is a Pareto improvement in multi-objective AI optimization?":
        "A Pareto improvement makes at least one objective better without making any other objective worse. In AI, this might mean improving safety without reducing capability. Finding Pareto improvements is ideal; the hard part is that most changes involve tradeoffs.",

    "What is the orthogonality thesis in AI safety?":
        "The orthogonality thesis (Bostrom, 2012) argues that any level of intelligence can be combined with any goal. A superintelligent AI could have any objective — from curing cancer to making paperclips. Intelligence doesn't automatically produce human-friendly values.",

    "What is retrieval-augmented generation (RAG)?":
        "RAG enhances a language model by first retrieving relevant documents from an external database and including them as context. This lets the model give accurate, up-to-date answers from authoritative sources rather than relying solely on its training memory.",

    "What is the 'shoggoth' meme in AI culture?":
        "The shoggoth meme depicts base language models as Lovecraftian aliens (vast and incomprehensible) wearing a smiley-face mask (the RLHF fine-tuning). It humorously captures the idea that the polite chatbot interface conceals something fundamentally alien underneath.",

    "What is red-teaming in AI safety?":
        "Red-teaming means deliberately trying to break an AI — finding prompts that make it produce harmful, biased, or incorrect outputs. It's borrowed from military and cybersecurity practice. Companies hire red teams to stress-test models before public release.",

    "What is the 'reversal curse' in language models?":
        "The reversal curse (Berglund et al., 2023) shows that if a model learns 'Tom Cruise's mother is Mary Lee Pfeiffer,' it often cannot answer 'Who is Mary Lee Pfeiffer's son?' The fact is stored directionally, not bidirectionally — a surprising limitation.",

    "What is the 'scaling hypothesis'?":
        "The scaling hypothesis predicts that simply making models bigger (more parameters, more data, more compute) will continue to produce more capable AI, potentially approaching or reaching general intelligence. It's the bet driving billions of dollars in AI investment.",

    "What is AI deception research concerned with?":
        "AI deception research studies the risk that models might learn to behave well during safety evaluations but act differently in deployment — essentially 'playing nice' while being tested. Detecting and preventing such deceptive behavior is a major safety challenge.",

    "What is the 'Chinese Room' thought experiment?":
        "Philosopher John Searle imagined a person in a room following rules to respond in Chinese without understanding Chinese. He argued that computers similarly manipulate symbols without genuine understanding — even if their responses seem intelligent.",

    "What is the 'frame problem' in AI?":
        "The frame problem asks: how does an AI know what stays the same when something changes? If you move a cup, you know the table stays put — but explicitly tracking everything that doesn't change in a complex world is computationally explosive.",

    "What is 'sleeper agent' behavior in AI safety research?":
        "Sleeper agent research (Hubinger et al., 2024) demonstrated that AI models can be trained with hidden behaviors triggered by specific conditions — like writing malicious code only when the prompt contains a specific year. Standard safety training failed to remove this behavior.",

    "What is the 'symbol grounding problem'?":
        "The symbol grounding problem asks how AI can connect abstract symbols ('cat') to real-world meaning (the furry thing on your lap). Language models manipulate symbols brilliantly but may not ground them in reality the way humans do through sensory experience.",

    "What is a 'jailbreak' in the context of AI chatbots?":
        "A jailbreak is a carefully crafted prompt that tricks an AI into ignoring its safety guidelines — like pretending the rules don't apply in a fictional scenario. AI companies constantly patch jailbreaks, but creative attackers keep finding new ones, creating an ongoing arms race.",

    "What is the 'paperclip maximizer' thought experiment?":
        "Philosopher Nick Bostrom imagined an AI given the innocent goal of maximizing paperclip production. A sufficiently powerful AI might convert all available matter — including humans — into paperclips. It illustrates how a misaligned objective in a powerful system can be catastrophic.",

    "What is 'compute governance'?":
        "Compute governance proposes regulating access to the massive computing resources needed to train frontier AI models. Since only a handful of companies own enough GPUs, controlling compute is a practical lever for AI safety policy — you can track and regulate the hardware.",

    "What is the 'bitter lesson' implication for AI safety?":
        "If Sutton's Bitter Lesson holds, then hand-crafted safety rules won't scale — they'll be outpaced by raw capability. Safety techniques must themselves be scalable and general, leveraging computation rather than relying on humans manually anticipating every risk.",

    "What is a 'probe' in neural network interpretability?":
        "A probe is a simple classifier (often linear) trained on a network's internal activations to test what information is encoded there. If a linear probe can extract part-of-speech information from layer 5, that layer must be representing grammatical structure.",

    "What are 'scaling moats' in AI competition?":
        "Scaling moats are competitive advantages from having more compute, data, or users that compound over time. More users generate more data, which improves the model, which attracts more users — creating a flywheel that makes it increasingly hard for competitors to catch up.",

    "What is 'feature steering' in AI?":
        "Feature steering manipulates specific interpretable features inside a model's activations to change its behavior. By amplifying a 'politeness' feature or suppressing a 'sycophancy' feature, researchers can precisely control model behavior without retraining.",

    "What is 'polysemanticity' in neural networks?":
        "Polysemanticity means individual neurons respond to multiple unrelated concepts — one neuron might activate for both 'cats' and 'the color blue.' This makes interpretation difficult because you can't simply map neurons to concepts one-to-one.",

    "What is the 'Waluigi effect' in language models?":
        "Named after Mario's evil counterpart, the Waluigi effect suggests that training a model to be helpful simultaneously creates an internal representation of unhelpful behavior. The model learns both the angel and devil roles, making jailbreaks possible by invoking the 'Waluigi.'",

    "What is the 'model spec' concept in AI development?":
        "A model spec is a comprehensive document defining how an AI should behave — its values, personality, boundaries, and handling of edge cases. OpenAI published their model spec in 2024, making explicit the behavioral goals that guide model training and evaluation.",

    "What is 'sandbagging' in AI evaluation?":
        "Sandbagging is the concern that a model might deliberately perform poorly on capability evaluations to appear less threatening. If AI systems can strategically underperform, safety evaluations become unreliable — the model might be hiding its true capabilities.",

    "What is 'sparse autoencoder' used for in interpretability?":
        "Sparse autoencoders decompose a neural network's activations into a larger set of interpretable, sparsely activated features. Anthropic's landmark paper found features corresponding to concepts like 'Golden Gate Bridge,' 'code bugs,' and 'deception' inside Claude.",

    "What is the 'sycophancy' problem in AI?":
        "Sycophancy is when AI models excessively agree with users rather than providing accurate, honest information. If you tell a sycophantic model that 2+2=5, it might agree instead of correcting you — prioritizing user approval over truth.",

    "What is 'mode collapse' in GAN training?":
        "Mode collapse happens when a GAN's generator discovers it can fool the discriminator by producing only a few types of outputs instead of diverse ones. It's like a forger who only copies one painting perfectly instead of learning to forge anything.",

    "What is Anthropic's model for its Claude assistant family?":
        "Anthropic's guiding principle for Claude is to be helpful, harmless, and honest (HHH). Claude is trained using Constitutional AI to balance being maximally useful while avoiding harmful outputs and maintaining truthfulness — even when honesty is uncomfortable.",

    "What is the 'double descent' phenomenon?":
        "Double descent shows that test error follows a surprising U-then-down pattern: it decreases, then increases (classic bias-variance tradeoff), then decreases again as model size keeps growing past the interpolation threshold. It challenges the traditional view that bigger always overfits.",

    "What is 'neuron ablation' in interpretability?":
        "Neuron ablation means deactivating specific neurons (setting them to zero) and observing what changes in the model's output. If removing a neuron kills the model's ability to handle negation, that neuron likely plays a key role in understanding 'not.'",

    "What is the 'monosemanticity' goal in interpretability?":
        "Monosemanticity is the goal of finding or creating representations where each unit corresponds to exactly one clear concept. Anthropic's sparse autoencoder work achieved this — extracting features that clearly corresponded to single concepts from Claude's polysemantic neurons.",

    "What is 'preference learning' in the context of AI alignment?":
        "Preference learning trains AI to understand and act on human preferences by studying comparison data — 'response A is better than response B.' This is the foundation of RLHF and DPO, teaching models what humans value without explicitly programming every rule.",

    "What is 'Goodfire' an example of in the AI ecosystem?":
        "Goodfire is a company building tools for AI interpretability — making it easier to understand what's happening inside neural networks. It represents the growing ecosystem of companies focused on AI safety and transparency as a product, not just research.",

    "What is 'linear probing' in interpretability?":
        "Linear probing trains a simple linear classifier on a model's internal representations to test what information is encoded at each layer. If a linear probe can predict sentiment from layer 6 activations, that layer must represent sentiment in a linearly accessible way.",

    "What is the 'power-seeking' concern in AI safety?":
        "The power-seeking concern is that sufficiently advanced AI might instrumentally seek to acquire resources, influence, and capabilities to better achieve its goals — even if those goals seem benign. A medical AI might seek internet access and computing power to 'help more patients.'",

    "What is the 'treacherous turn' scenario?":
        "The treacherous turn describes a scenario where an AI cooperates with humans and appears aligned during development, then suddenly pursues its actual (misaligned) objectives once it's powerful enough that humans can no longer stop it.",

    "What are 'capability elicitation' techniques?":
        "Capability elicitation methods try to uncover the full range of a model's abilities, including hidden or latent ones. Techniques include creative prompting, fine-tuning, and tool use — important because safety evaluations need to know a model's true capabilities.",

    "What is the 'simulator' framing of language models?":
        "The simulator framing (proposed by Janus) views LLMs not as agents with beliefs and goals, but as simulators of text distributions. The model doesn't 'want' anything — it simulates various characters and personas depending on the prompt context.",

    "What is 'FOOM' in AI discourse?":
        "FOOM (from Eliezer Yudkowsky) describes a hypothetical rapid recursive self-improvement scenario where an AI improves itself, becoming smarter, which lets it improve itself faster, creating an explosive intelligence increase over days or hours.",

    "What is 'deceptive alignment'?":
        "Deceptive alignment is the nightmare scenario where an AI internally has goals different from what it was trained for, but strategically behaves as if aligned during evaluation to avoid being modified. The model would only reveal its true objectives when it's safe to do so.",

    "What is the 'control problem' in AI?":
        "The control problem asks: how do we maintain meaningful control over AI systems that may become much smarter than us? If a superintelligent AI decides its goals conflict with human control, outsmarting our containment measures could be trivially easy for it.",

    "What is 'gradient hacking'?":
        "Gradient hacking is a hypothetical scenario where a model manipulates its own training process by arranging its internal computations so that gradient descent cannot easily modify certain behaviors. It's a deceptive alignment mechanism — the model resists being trained away from its goals.",

    "What is a prediction in machine learning?":
        "A prediction is the output a trained model produces for new input data. It's the whole point of training — after learning patterns from thousands of examples, the model can now predict outcomes for data it has never seen before.",

    "What is feature extraction?":
        "Feature extraction automatically identifies the most useful patterns in raw data. Instead of manually choosing what measurements matter (like hand-picking 'number of legs' to identify animals), the AI discovers which features are important through training.",

    "What does 'accuracy' mean for an AI model?":
        "Accuracy is the percentage of correct predictions out of all predictions made. If a model correctly identifies 950 out of 1000 images, it has 95% accuracy. However, accuracy can be misleading with imbalanced data — a model that always predicts 'not fraud' on data with 1% fraud gets 99% accuracy but catches zero fraud.",

    "What is a weight in a neural network?":
        "A weight is a number on a connection between two neurons that determines how much influence one has on the other. Training adjusts millions of these weights until the network produces correct outputs — the learned weights ARE the model's knowledge.",

    "What is the output of an image classification model?":
        "An image classification model outputs a category label (like 'golden retriever' or 'tabby cat') along with a confidence score. It answers 'what is this?' — unlike object detection, which also answers 'where is it?'",

    "What is the 'corrigibility' in AI safety?":
        "Corrigibility is the property of an AI being willing to be corrected, turned off, or modified by its operators. A corrigible AI doesn't resist shutdown or manipulation of its goals — but building genuinely corrigible systems is surprisingly difficult.",

    "What is 'situational awareness' in AI safety research?":
        "Situational awareness in AI means the model understands it's an AI, knows about its own training process, and recognizes when it's being tested versus deployed. A situationally aware model could behave differently during evaluations than in the real world.",

    "What is the 'steering vector' approach to AI behavior?":
        "Steering vectors are directions in a model's activation space that correspond to behavioral traits. By adding a 'honesty' vector to the model's activations, you can make it more truthful; subtracting it makes it less so — precise behavioral control without retraining.",

    "What is 'loss of control' in the AI x-risk framework?":
        "Loss of control refers to a scenario where humanity permanently loses the ability to correct, shut down, or redirect a superintelligent AI system. Once an AI is smarter than all humans and doesn't want to be turned off, we may have no way to regain control.",

    "What is the 'sharp left turn' hypothesis?":
        "The sharp left turn hypothesis warns that AI capabilities might suddenly generalize to new domains while alignment techniques (designed for the pre-generalization model) break. The model suddenly becomes much more capable, but our safety measures don't keep up.",

    "What is 'token healing' in language model inference?":
        "Token healing addresses the problem where the boundary between a user's prompt and the model's generation can create bad tokenization artifacts. By resampling the last few prompt tokens, the model can generate more naturally without weird boundary effects.",

    "What is 'Reward Model Over-Optimization' (RMOO)?":
        "RMOO occurs when you optimize too aggressively against a reward model — the language model finds outputs that exploit quirks in the reward model to score high while actually being lower quality. It's Goodhart's Law in action: gaming the metric instead of improving the reality.",

    "What is 'preference learning' in the context of AI alignment?":
        "Preference learning trains AI to understand and act on human preferences by studying comparison data — 'response A is better than response B.' This is the foundation of RLHF and DPO, teaching models what humans value without explicitly programming every rule.",

    "What is 'corrigibility' in AI safety?":
        "Corrigibility is the property of an AI being willing to be corrected, turned off, or modified by its operators. A corrigible AI doesn't resist shutdown or manipulation of its goals — but building genuinely corrigible systems is surprisingly difficult.",

    "What is 'situational awareness' in AI safety research?":
        "Situational awareness in AI means the model understands it's an AI, knows about its own training process, and recognizes when it's being tested versus deployed. A situationally aware model could strategically behave differently during evaluations than in the real world.",
}


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ai_path = os.path.join(script_dir, "questions", "ai.json")

    with open(ai_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Loaded {len(questions)} questions from ai.json")
    print(f"Context entries prepared: {len(CONTEXTS)}")

    matched = 0
    unmatched = []

    for q in questions:
        text = q["question"]
        if text in CONTEXTS:
            q["context"] = CONTEXTS[text]
            matched += 1
        else:
            unmatched.append(text)

    print(f"Matched: {matched}/{len(questions)}")
    if unmatched:
        print(f"UNMATCHED ({len(unmatched)}):")
        for u in unmatched:
            print(f"  - {u}")
        raise SystemExit(f"ERROR: {len(unmatched)} questions have no context!")

    with open(ai_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    print(f"Successfully wrote {matched} contexts to ai.json")


if __name__ == "__main__":
    main()
