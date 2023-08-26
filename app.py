import streamlit as st
import json
import requests
from typing import Dict, List

from langchain.llms import OpenAI
from langchain.agents import AgentExecutor, AgentType, initialize_agent, load_tools  # type: ignore
from langchain.tools import BaseTool

from schemas import Discover, Course


def getDescriptionAndWiki(topic: str) -> Dict[str, str]:
    # Create a new instance of the OpenAI class
    llm = OpenAI(
        openai_api_key=st.secrets["OPENAI_API_KEY"],
        max_tokens=200,
        temperature=0,
        client=None,
        model="text-davinci-003",
        frequency_penalty=1,
        presence_penalty=0,
        top_p=1,
    )

    # Load the tools
    tools: List[BaseTool] = load_tools(["google-serper"], llm=llm)

    # Create a new instance of the AgentExecutor class
    agent: AgentExecutor = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=False,
    )

    # Create the template
    template = """I need information about the following topic: {topic}. Give the explanation in a json format as {{"description": The description of the topic, "url": Any page to learn more about this topic}}"""

    # Generate the response
    response: str = agent.run(template.format(topic=topic))

    # Print the response
    print(response)

    # Convert the response to a dictionary
    result = json.loads(response)

    return result


def getCourses(topic: str) -> List[Course]:
    """
    Get links from Serper API
    """

    # Set Serper API URL
    url = st.secrets["SERPER_API_URL"]

    # Set Serper API headers
    headers = {
        "X-API-KEY": st.secrets["SERPER_API_KEY"],
        "Content-Type": "application/json",
    }

    # Fix query parameters
    payload = json.dumps({"q": f"{topic} Courses"})

    # Get response from Serper API
    response = requests.request("POST", url, headers=headers, data=payload)  # type: ignore
    response_dict = response.json()

    # Get links from response
    links: List[Course] = []

    for result in response_dict["organic"]:
        cr: Course = Course(
            topic=result["title"],
            url=result["link"],
            description=result["snippet"],
        )
        links.append(cr)

    # Print links
    print(links)

    return links


def discover_API(topic: str) -> Discover:
    """
    Discover a topic
    """
    # Get description and wiki
    result = getDescriptionAndWiki(topic)

    # Create response
    response: Discover = Discover(
        topic=topic,
        description=result["description"],  # type: ignore
        url=result["url"],  # type: ignore
        courses=getCourses(topic),
    )

    return response


st.title("Course Compass")

# Put a line under the title
st.markdown("---")

# Add an input field
topic = st.text_input("Enter the topic")

# Add a button
if st.button("Submit"):
    # Call the API
    response: Discover = discover_API(topic)

    # Display the description
    st.title("Description")
    st.write(response.description)  # type: ignore

    # Display the url
    st.write("To Learn More Visit")  # type: ignore
    st.write(response.url)  # type: ignore

    st.markdown("---")

    # Display the courses one by one
    st.title("Courses")

    for course in response.courses:  # type: ignore
        st.write("**Title:**")  # type: ignore
        st.write(course.topic)  # type: ignore

        st.write("**Description:**")  # type: ignore
        st.write(course.description)  # type: ignore

        st.write("**URL:**")  # type: ignore
        st.write(course.url)  # type: ignore

        st.markdown("---")
