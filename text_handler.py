import os
from dotenv import load_dotenv
from openai import OpenAI, APIError
import httpx
from logger_config import setup_logger

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Setup logger
logger = setup_logger('text_handler', 'text_handler.log')

def correct_text(text: str, level: str, conversation_history: list = None) -> str:
    """
    Process user text and return AI response with natural corrections if needed.
    conversation_history: list of tuples (role, message)
    """
    try:
        # Handle topic-specific questions
        if text.startswith("generate_topic_question_"):
            topic = text.replace("generate_topic_question_", "")
            return generate_topic_question(topic, level)

        # Create a prompt that encourages natural, conversational corrections
        system_prompt = f"""You are a friendly English tutor having a conversation with a {level}-level English learner. 
        When responding:
        1. Reply naturally to keep the conversation flowing
        2. Always include:
           - A response to what they said
           - A relevant follow-up question to keep the conversation going
        3. If there are language mistakes:
           - Identify what could be improved
           - Suggest more natural alternatives
           - Explain why the changes make it more natural (briefly)
        4. Use common, everyday expressions appropriate for their {level} level
        5. Match the formality level to the context
        6. Only correct if the change helps them improve their English
        7. Consider the conversation context when responding
        
        Format your response as:
        AI: [your response to their message + a follow-up question]
        
        Corrected: [if needed, explain improvements and provide better alternatives]
        Example correction format:
        - Original: "I am very tired because I slept very late yesterday"
        - Better: "I'm really tired because I went to bed late last night"
        - Why: Using "I'm" is more natural in conversation, and "went to bed" is the common way to express sleeping time
        """

        # Start with the system message
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if available
        if conversation_history:
            for role, content in conversation_history:
                # Convert our role format to OpenAI's format
                openai_role = "assistant" if role == "assistant" else "user"
                messages.append({"role": openai_role, "content": content})
        
        # Add the current message
        messages.append({"role": "user", "content": text})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=300,
            timeout=30
        )

        return response.choices[0].message.content

    except (httpx.ConnectTimeout, httpx.ReadTimeout):
        logger.error("Timeout connecting to OpenAI API")
        return "AI: I'm sorry, I'm having trouble connecting right now. Could you please try again in a moment?"
    
    except APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return "AI: I encountered an error. Please try again."
    
    except Exception as e:
        logger.error(f"Unexpected error in correct_text: {str(e)}")
        return "AI: I'm sorry, something went wrong. Please try again later."

def generate_topic_question(topic: str, level: str) -> str:
    """
    Generate a natural conversation starter for the chosen topic.
    """
    system_prompt = f"""You are a friendly English tutor starting a conversation about {topic} with a {level}-level English learner.
    Generate an engaging, level-appropriate question to start the conversation.
    Make it natural and conversational, as if you're chatting with a friend.
    
    Format your response as:
    AI: [your conversation-starting question]"""

    conversation = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Start a conversation about {topic}"}
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation,
        temperature=0.7,
        max_tokens=150
    )

    return response.choices[0].message.content