import os
import speech_recognition as sr
from pydub import AudioSegment
from openai import OpenAI

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

def process_voice_message(voice_file_path, level):
    """Process voice message: transcribe, respond conversationally, and correct if needed."""
    try:
        # Convert OGG to WAV
        wav_file_path = convert_ogg_to_wav(voice_file_path)
        
        # Transcribe audio
        transcribed_text = transcribe_audio(wav_file_path)
        
        # Clean up WAV file
        os.remove(wav_file_path)
        
        if not transcribed_text:
            return "AI: I couldn't understand the audio. Could you try again with clearer audio?"
        
        # Level-specific context
        level_context = {
            "beginner": "Focus on basic pronunciation, simple grammar and vocabulary.",
            "intermediate": "Correct grammar, vocabulary, and suggest natural speech patterns.",
            "advanced": "Focus on accent reduction, fluency, and native-like expressions."
        }
        
        context = level_context.get(level, level_context["intermediate"])
        
        # Get response and correction using AI
        prompt = f"""
        You are an AI English tutor having a conversation with a {level} level English learner.
        
        I transcribed their spoken English as: "{transcribed_text}"
        
        Respond in three parts:
        1. First, confirm what you heard
        2. Give a natural conversational response to what they said (about 1-3 sentences)
        3. If there are any language issues, provide a corrected version
        
        Guidelines:
        - {context}
        - Only provide a correction if there are actual errors or significant improvements to be made
        - If their English is already good, skip the correction part
        - Keep the conversation friendly and encouraging
        
        Format your response as:
        "I heard: [transcribed text]
        
        AI: [your conversational response]
        
        Corrected: [corrected version]"
        
        If no correction is needed, skip the "Corrected:" part.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an English language tutor having a friendly conversation while helping students improve their speaking."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error processing voice message: {e}")
        return "AI: I'm sorry, I couldn't process your voice message. Could you try again?"