from __future__ import annotations

import json
from typing import Any, List, Optional

from crewai import Agent, Crew, Process, Task
from crewai.tools import tool

from agents import run_researcher, run_strategist, run_copywriter, run_director, run_designer, run_market_intelligence


@tool("meta_ads_researcher_tool")
def researcher_tool(query: str) -> str:
    """Scrapes Meta ads for a given search query and returns the path to the results JSON."""
    return run_researcher(search_query=query)


@tool("market_intelligence_tool")
def market_intelligence_tool(query: str) -> str:
    """Performs advanced web searching across YouTube, X, and Reddit to gather market signals and source weights."""
    return run_market_intelligence(query=query)


@tool("marketing_strategist_tool")
def strategist_tool(ads_path: str) -> str:
    """Performs a deep 'Why/How/What' analysis on a JSON file of ads to identify psychological triggers and structural patterns."""
    return run_strategist(ads_path=ads_path)


@tool("video_copywriter_tool")
def copywriter_tool(strategy_path: str, market_data_path: Optional[str] = None) -> str:
    """Generates a high-converting video script by blending proven ad patterns with current market signal data."""
    return run_copywriter(marketing_strategy_path=strategy_path, market_data_path=market_data_path)


@tool("video_designer_tool")
def designer_tool(script_path: str) -> str:
    """Creates a visual design specification (colors, layout, animations) tailored to the script's emotional tone."""
    return run_designer(script_path=script_path)


@tool("video_director_tool")
def director_tool(script_path: str) -> str:
    """Elevates the script with cinematic direction and coordinates the generation of all media assets."""
    return run_director(script_path=script_path)


class MarketingVideoCrew:
    def __init__(self, market_data_path: Optional[str] = None):
        self.market_data_path = market_data_path
        self.researcher = Agent(
            role="Ad Researcher",
            goal="Identify and scrape top-performing Meta ads for specific niches.",
            backstory="You are an expert at uncovering the visual and narrative trends that dominate social media feeds.",
            tools=[researcher_tool],
            verbose=True,
            allow_delegation=False,
        )

        self.analyst = Agent(
            role="Market Analyst",
            goal="Gather and distill broad market intelligence from YouTube, X, and Reddit.",
            backstory="You are a social sentiment expert who can distinguish between market noise and genuine signals.",
            tools=[market_intelligence_tool],
            verbose=True,
            allow_delegation=False,
        )

        self.strategist = Agent(
            role="Ad Psychologist & Strategist",
            goal="Deconstruct ads to find the 'Why' (psychology), 'How' (structure), and 'What' (offer).",
            backstory="You don't just see ads; you see the invisible levers of persuasion that drive human behavior.",
            tools=[strategist_tool],
            verbose=True,
            allow_delegation=False,
        )

        self.copywriter = Agent(
            role="Master Direct-Response Copywriter",
            goal="Write cinematic scripts that weave market 'signals' into proven psychological ad frameworks.",
            backstory="You combine the cold logic of market data with the emotional heat of top-tier copywriting.",
            tools=[copywriter_tool],
            verbose=True,
            allow_delegation=False,
        )

        self.director = Agent(
            role="Cinematic Video Director",
            goal="Ensure visual continuity, emotional pacing, and high-quality asset execution.",
            backstory="You turn scripts into visual experiences, focusing on lighting, metaphor, and technical perfection.",
            tools=[director_tool, designer_tool],
            verbose=True,
            allow_delegation=False,
        )

    def run(self, topic: str):
        task1 = Task(
            description=f"Research and scrape successful ads for the topic: {topic}",
            agent=self.researcher,
            expected_output="Path to the JSON file containing scraped ads.",
        )
        task2 = Task(
            description=f"Gather multi-source market intelligence for {topic} to identify social sentiment and source weights.",
            agent=self.analyst,
            expected_output="Path to the distilled Market Signal JSON file.",
        )
        task3 = Task(
            description="Perform a deep Why/How/What analysis of the researched ads to identify winning psychological and structural patterns.",
            agent=self.strategist,
            expected_output="Path to the comprehensive marketing strategy JSON file.",
        )
        task4 = Task(
            description=f"Write a 6-scene high-converting video script. Weave the market intelligence signals into the proven ad frameworks.",
            agent=self.copywriter,
            expected_output="Path to the final script JSON file.",
        )
        task5 = Task(
            description="Elevate the script with cinematic direction and generate all necessary visual and audio assets for Remotion.",
            agent=self.director,
            expected_output="Path to the final Remotion props JSON file.",
        )

        crew = Crew(
            agents=[self.researcher, self.analyst, self.strategist, self.copywriter, self.director],
            tasks=[task1, task2, task3, task4, task5],
            process=Process.sequential,
            verbose=True,
        )

        return crew.kickoff()
