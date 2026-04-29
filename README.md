VARmageddon AI (VAR-Ref-Oracle)
VARmageddon AI is an automated regulatory analysis tool designed for football match officials. It uses generative AI to provide real-time interpretations of the IFAB Laws of the Game and specific league handbooks (like the Bundesliga) while automatically tracking disciplinary actions.

🚀 Key Features
Automated Match Ledger: Automatically logs yellow and red cards to a session sidebar using smart regex extraction to prevent duplicates.

Voice-to-Ruling: Integrated voice input for hands-free incident reporting by officials.

Regulatory Hierarchy: Designed to cross-reference multiple rulebooks, correctly identifying league-specific rules (e.g., Bundesliga 5th-yellow suspension) over general UEFA rules.

Multi-Language Support: Capable of providing technical rulings in English, Portuguese, German, and more.

🛠️ Technical Stack
Frontend: Streamlit

AI Engine: Amazon Bedrock (Nova Micro 1.0)

Cloud Storage: Amazon S3 (Knowledge Base for PDFs)

Audio Processing: pydub and SpeechRecognition
