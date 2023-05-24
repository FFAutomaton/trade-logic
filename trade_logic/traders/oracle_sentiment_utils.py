from datetime import datetime, timezone, timedelta


def generate_summary(obj, input_text):
    # prompt = f"""Assume that you are a crypto investor.
    #     Analyze the market behaviour as positive, negative or neutral.
    #     Prompt only the result, use one word.
    #     """
    prompt = f"""Summarize the below text not less than 200 words:
                {input_text}"""
    response = obj.client.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                'role': 'user',
                'content': prompt,
            }
        ]
    )
    summary = response.choices[0].message.content
    return summary

def translate_titles(obj, input_text):
    prompt = f"Please translate the following text to English:\n{input_text}\nTranslation:"
    response = obj.client.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                'role': 'user',
                'content': prompt,
            }
        ]
    )
    summary = response.choices[0].message.content
    return summary