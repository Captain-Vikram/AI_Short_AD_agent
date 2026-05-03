from __future__ import annotations

import json
from typing import Any, List, Optional

from crewai import Agent, Crew, Process, Task
from crewai.tools import tool

from agents import run_researcher, run_strategist, run_copywriter, run_director, run_designer


@tool("meta_ads_researcher_tool")
def researcher_tool(query: str) -> str:
    """Scrapes Meta ads for a given search query and returns the path to the results JSON."""
    return run_researcher(search_query=query)


@tool("marketing_strategist_tool")
def strategist_tool(ads_path: str) -> str:
    """Analyzes a JSON file of ads and returns a marketing strategy JSON path."""
    return run_strategist(ads_path=ads_path)


@tool("video_copywriter_tool")
def copywriter_tool(strategy_path: str) -> str:
    """Generates a video script JSON from a marketing strategy path."""
    return run_copywriter(marketing_strategy_path=strategy_path)


@tool("video_designer_tool")
def designer_tool(script_path: str) -> str:
    """Creates a visual design specification from a video script path."""
    return run_designer(script_path=script_path)


@tool("video_director_tool")
def director_tool(script_path: str) -> str:
    """Generates all media assets (images, audio, subtitles) and returns the Remotion props path."""
    return run_director(script_path=script_path)


class MarketingVideoCrew:
    def __init__(self):
        self.researcher = Agent(
            role="Ad Researcher",
            goal="Find successful marketing ads for specific niches",
            backstory="You are an expert at identifying winning ad patterns on social media.",
            tools=[researcher_tool],
            verbose=True,
            allow_delegation=False,
        )

        self.strategist = Agent(
            role="Marketing Strategist",
            goal="Extract hooks and pain points from ad data",
            backstory="You turn raw data into actionable marketing strategies.",
            tools=[strategist_tool],
            verbose=True,
            allow_delegation=False,
        )

        self.copywriter = Agent(
            role="Video Copywriter",
            goal="Write high-converting scripts based on strategy",
            backstory="You are a master of persuasion and short-form video storytelling.",
            tools=[copywriter_tool],
            verbose=True,
            allow_delegation=False,
        )

        self.director = Agent(
            role="Video Director",
            goal="Coordinate asset generation and technical execution",
            backstory="You ensure every script is brought to life with the right visuals and audio.",
            tools=[director_tool, designer_tool],
            verbose=True,
            allow_delegation=False,
        )

    def run(self, topic: str):
        task1 = Task(
            description=f"Research top ads for the topic: {topic}",
            agent=self.researcher,
            expected_output="Path to the JSON file containing scraped ads.",
        )
        task2 = Task(
            description="Create a marketing strategy based on the researched ads.",
            agent=self.strategist,
            expected_output="Path to the marketing strategy JSON file.",
        )
        task3 = Task(
            description="Write a video script based on the marketing strategy.",
            agent=self.copywriter,
            expected_output="Path to the script JSON file.",
        )
        task4 = Task(
            description="Generate all assets and prepare the video for rendering.",
            agent=self.director,
            expected_output="Path to the final Remotion props JSON file.",
        )

        crew = Crew(
            agents=[self.researcher, self.strategist, self.copywriter, self.director],
            tasks=[task1, task2, task3, task4],
            process=Process.sequential,
            verbose=True,
        )

        return crew.kickoff()
