import os
import speech_recognition as sr
from pydub import AudioSegment
from openai import OpenAI
from gtts import gTTS
import tempfile
from logger_config import setup_logger
from utils import retry_on_timeout

# Setup logger
logger = setup_logger('speech_handler', 'speech_handler.log')

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def convert_ogg_to_wav(ogg_file_path):
    """Convert OGG file to WAV format for speech recognition."""
    wav_file_path = ogg_file_path.replace(".ogg", ".wav")
    audio = AudioSegment.from_ogg(ogg_file_path)
    audio.export(wav_file_path, format="wav")
    return wav_file_path

def transcribe_audio(audio_file_path):
    """Transcribe audio file to text using speech recognition."""
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(audio_file_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            return text
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

@retry_on_timeout(max_retries=3)
def process_voice_message(file_path: str, level: str) -> tuple[str, str | None]:
    """Process voice message and return both text response and path to correction audio."""
    wav_path = None
    try:
        logger.info(f"Processing voice message - file: {file_path}, level: {level}")
        
        # Convert ogg to wav
        audio = AudioSegment.from_ogg(file_path)
        wav_path = tempfile.mktemp(suffix='.wav')
        audio.export(wav_path, format="wav")
        logger.info("Converted audio to WAV format")
        
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            try:
                # Transcribe audio
                logger.info("Transcribing audio with Google Speech Recognition")
                transcribed_text = recognizer.recognize_google(audio_data)
                logger.info(f"Audio transcribed: {transcribed_text[:50]}...")
            except sr.UnknownValueError:
                logger.warning("Google Speech Recognition could not understand the audio")
                return ("I'm sorry, I couldn't understand what you said. Could you please speak more clearly or try again in a quieter environment?", None)
            except sr.RequestError as e:
                logger.error(f"Could not request results from Speech Recognition service: {str(e)}")
                return ("I'm having trouble connecting to the speech recognition service. Please try again later.", None)
            
            # Get AI response and correction
            logger.info("Sending transcription to OpenAI API")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"""You are a friendly English tutor helping a {level}-level learner with pronunciation and speaking.
                    When responding:
                    1. Acknowledge what you heard
                    2. Provide a natural response
                    3. If there are pronunciation issues, provide ONLY the corrected version of what they said with phonetic spelling
                    
                    Format your response as:
                    I heard: [transcribed text]
                    
                    AI: [your response]
                    
                    Corrected: [ONLY the user's exact words with phonetic spelling for correction, no additional explanations]"""},
                    {"role": "user", "content": transcribed_text}
                ]
            )
            logger.info("Received response from OpenAI API")
            
            result = response.choices[0].message.content
            
            # Generate correction audio if needed
            correction_audio_path = None
            if "Corrected:" in result:
                correction_text = result.split("Corrected:")[1].strip()
                if correction_text:
                    logger.info("Generating correction audio with gTTS")
                    correction_audio_path = tempfile.mktemp(suffix='.mp3')
                    tts = gTTS(text=correction_text, lang='en', slow=True)
                    tts.save(correction_audio_path)
                    logger.info("Correction audio generated")
            
            # Clean up wav file
            os.remove(wav_path)
            logger.info("Temporary WAV file cleaned up")
            
            return result, correction_audio_path
            
    except Exception as e:
        logger.error(f"Error processing voice message: {str(e)}")
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
        raise