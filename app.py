import streamlit as st
import json
import requests
from typing import Dict, List
from streamlit_option_menu import option_menu  # type: ignore

from PyPDF2 import PdfReader

from pymongo import MongoClient

from langchain.llms import OpenAI
from langchain.agents import AgentExecutor, AgentType, initialize_agent, load_tools  # type: ignore
from langchain.tools import BaseTool

from schemas import Discover, Course

client = MongoClient(st.secrets["DB_URI"])  # type: ignore
db = client["CourseCompass"]  # type: ignore
collection = db["data"]  # type: ignore


def store(result: dict[str, str | list[dict[str, str]]]):
    """
    Store the result in the database
    """
    collection.insert_one(result)  # type: ignore


def ifExists(topic: str) -> Discover | None:
    """
    Check if the topic exists in the database and return it
    """
    result = collection.find_one({"topic": topic})  # type: ignore

    if result == None:
        return None

    # Convert the courses to a list of Course objects
    courses: List[Course] = []

    for r in result["courses"]:  # type: ignore
        cr: Course = Course(
            topic=r["topic"],  # type: ignore
            url=r["url"],  # type: ignore
            description=r["description"],  # type: ignore
        )
        courses.append(cr)

    # Create Discover object
    response: Discover = Discover(
        topic=result["topic"],  # type: ignore
        description=result["description"],  # type: ignore
        url=result["url"],  # type: ignore
        courses=courses,
    )

    return response


def getDescriptionAndWiki(topic: str) -> Dict[str, str]:
    """
    Get the description about the topic and a link to know more about it
    """
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
        verbose=True,
    )

    # Create the template
    template = """I need information about the following topic: {topic}. Give the explanation in a json format as {{"description": The description of the topic, "url": Any page to learn more about this topic}}"""

    # Generate the response
    response: str = agent.run(template.format(topic=topic))

    # Convert the response to a dictionary
    result = json.loads(response)

    return result


def getCourses(topic: str) -> list[dict[str, str]]:
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

    return response_dict


def discover_API(topic: str) -> Discover:
    """
    Discover a topic
    """
    # Remove spaces and convert to lowercase
    topic_db = topic.lower().replace(" ", "")

    # Extract the details if in db
    db = ifExists(topic_db)

    # Check if topic exists in db and return it
    if db != None:
        print("Topic found in DB")
        return db

    # Get description and links
    result = getDescriptionAndWiki(topic)
    result_courses = getCourses(topic)

    # Convert the links to a list of Course objects
    links: List[Course] = []

    for r in result_courses["organic"]:  # type: ignore
        cr: Course = Course(
            topic=r["title"],  # type: ignore
            url=r["link"],  # type: ignore
            description=r["snippet"],  # type: ignore
        )
        links.append(cr)

    courses: list[dict[str, str]] = []

    # Convert the links to a list of dictionaries
    for r in result_courses["organic"]:  # type: ignore
        courses.append({"topic": r["title"], "url": r["link"], "description": r["snippet"]})  # type: ignore

    # Store the result in the database
    store(
        {
            "topic": topic_db,
            "description": result["description"],
            "url": result["url"],
            "courses": courses,
        }
    )

    # Create response
    response: Discover = Discover(
        topic=topic_db,
        description=result["description"],  # type: ignore
        url=result["url"],  # type: ignore
        courses=links,
    )

    return response


# Add a title
st.title("Course Compass")

# # Put a line under the title
# st.markdown("---")

# Create tabs
tabs = st.tabs(["Discover Courses", "Extract Text"])

# Discover page
with tabs[0]:
    # Add an input field
    topic = st.text_input("Enter the topic")

    if st.button("Submit"):
        # Call the API
        response = discover_API(topic)

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

# Extract page
with tabs[1]:
    # add a file input
    file = st.file_uploader("Upload your material")

    if st.button("Upload "):
        pdf = PdfReader(file)  # type: ignore

        text = ""

        # Extract text from the pdf
        for page in pdf.pages:
            text += page.extract_text()

        if text != "":
            st.title("Contents of your Material : ")
            st.write(text)  # type: ignore
