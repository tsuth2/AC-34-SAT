from openai import OpenAI
import os

def api_response(transcription):
  client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

  completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": "You are speaking to somebody on the phone that is discussing computer issues, and are purposely being unhelpful to them because they are a scammer."},
      {"role": "user", "content": [{"type": "text", "text": f"{transcription}"}]} #"Compose a poem that explains the concept of recursion in programming."}
    ]
  )

  return completion


if __name__ == "__main__":
    transcription = "Sigma!"
    completion = api_response(transcription)
    print(completion.choices[0].message)