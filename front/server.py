#!/usr/bin/env python3
"""
US Hackathon Scanner — Local Backend Server
Run: python server.py
Then open: http://localhost:8000
"""

import http.server
import socketserver
import json
import urllib.request
import ssl
from datetime import datetime

PORT = 8000

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

FALLBACK_DATA = [
    {
    'name': 'GenZ Can Hack 2026',
    'website': 'https://genz-can-hack-2026.devpost.com/',
    'start': '2026-04-01T00:00:00Z',
    'end': '2026-08-22T23:59:00Z',
    'city': 'Toronto',
    'state': 'Ontario',
    'country': 'Canada',
    'countryCode': 'CA',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Build with Gemini XPRIZE',
    'website': 'https://xprize.devpost.com/',
    'start': '2026-05-19T00:00:00Z',
    'end': '2026-08-17T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'VoltHacks',
    'website': 'https://volthacks.devpost.com/',
    'start': '2026-05-22T00:00:00Z',
    'end': '2026-09-05T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Arm Create: AI Optimization Challenge',
    'website': 'https://arm-ai-optimization-challenge.devpost.com/',
    'start': '2026-06-04T00:00:00Z',
    'end': '2026-08-14T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Brainwave 2026',
    'website': 'https://brainwaves.devpost.com/',
    'start': '2026-06-12T00:00:00Z',
    'end': '2026-08-09T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'AceSAT Education AI-Agent',
    'website': 'https://acesat-ai-agent.devpost.com/',
    'start': '2026-06-12T00:00:00Z',
    'end': '2026-08-15T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Africa Deep Tech Challenge 2026',
    'website': 'https://adtc-2026.devpost.com/',
    'start': '2026-06-17T00:00:00Z',
    'end': '2026-08-25T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'AI YES :International Youth AI Competition',
    'website': 'https://ai-yes-competition-30441.devpost.com/',
    'start': '2026-06-17T00:00:00Z',
    'end': '2026-09-01T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Build Beyond Hackathon',
    'website': 'https://build-beyond-hackathon.devpost.com/',
    'start': '2026-06-18T00:00:00Z',
    'end': '2026-08-16T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Hack The Limit',
    'website': 'https://hack-the-limit-1.devpost.com/',
    'start': '2026-06-18T00:00:00Z',
    'end': '2026-08-30T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'NeuralSprint',
    'website': 'https://neuralsprint.devpost.com/',
    'start': '2026-06-18T00:00:00Z',
    'end': '2026-08-24T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'ImpactForge',
    'website': 'https://impactforge.devpost.com/',
    'start': '2026-06-19T00:00:00Z',
    'end': '2026-08-24T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Vitalitics 2026',
    'website': 'https://vitalitics26.devpost.com/',
    'start': '2026-06-20T00:00:00Z',
    'end': '2026-08-05T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'QuantumHacks',
    'website': 'https://quantumhacks.devpost.com/',
    'start': '2026-06-21T00:00:00Z',
    'end': '2026-08-20T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': '3D Websites Hackathon',
    'website': 'https://3d-websites-hackathon.devpost.com/',
    'start': '2026-06-22T00:00:00Z',
    'end': '2026-08-31T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Girls In STEM Global Hackathon',
    'website': 'https://girlsinstemhackathon.devpost.com/',
    'start': '2026-06-23T00:00:00Z',
    'end': '2026-08-05T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'The Rice University Urban Sustainability Hackathon',
    'website': 'https://rice-urban-sustainability.devpost.com/',
    'start': '2026-06-23T00:00:00Z',
    'end': '2026-09-18T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'DSH Pitch',
    'website': 'https://dsh-pitch-30500.devpost.com/',
    'start': '2026-06-24T00:00:00Z',
    'end': '2026-10-25T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'CockroachDB × AWS Hackathon',
    'website': 'https://cockroachdb-ai.devpost.com/',
    'start': '2026-06-30T00:00:00Z',
    'end': '2026-08-18T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'ML Empowerment Build Challenge 2.0',
    'website': 'https://ml-empowerment-2.devpost.com/',
    'start': '2026-06-30T00:00:00Z',
    'end': '2026-08-15T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Hackonomics 2027',
    'website': 'https://hackonomics27.devpost.com/',
    'start': '2026-07-01T00:00:00Z',
    'end': '2026-08-07T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Build with DataHub: The Agent Hackathon',
    'website': 'https://datahub.devpost.com/',
    'start': '2026-07-06T00:00:00Z',
    'end': '2026-08-10T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'YouCam API Skin AI & Apparel VTO Hackathon',
    'website': 'https://youcam-api.devpost.com/',
    'start': '2026-07-06T00:00:00Z',
    'end': '2026-08-17T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'CSC Summer Impactathon',
    'website': 'https://csc-summer-impactathon.devpost.com/',
    'start': '2026-07-09T00:00:00Z',
    'end': '2026-08-10T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'NextGen Innovation2026',
    'website': 'https://nextgen-innovation-2026.devpost.com/',
    'start': '2026-07-11T00:00:00Z',
    'end': '2026-08-08T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Galuxium Nexus V2',
    'website': 'https://galuxium-nexus-v2-29411.devpost.com/',
    'start': '2026-07-15T00:00:00Z',
    'end': '2026-08-31T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Build with Paritok',
    'website': 'https://build-with-paritok.devpost.com/',
    'start': '2026-07-20T00:00:00Z',
    'end': '2026-08-05T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'CALL-E: Your Code Is Calling',
    'website': 'https://call-e.devpost.com/',
    'start': '2026-07-23T00:00:00Z',
    'end': '2026-09-14T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'NEXORA Global Hackathon',
    'website': 'https://nexora-global-hackathon.devpost.com/',
    'start': '2026-07-23T00:00:00Z',
    'end': '2026-08-15T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'RLC Hacks 2026',
    'website': 'https://rlc-hacks-30705.devpost.com/',
    'start': '2026-07-26T00:00:00Z',
    'end': '2026-08-04T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Agentic Cinema: The Blockbuster Hackathon',
    'website': 'https://agentic-cinema.devpost.com/',
    'start': '2026-07-27T00:00:00Z',
    'end': '2026-09-07T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Caspian Buildathon',
    'website': 'https://caspian.devpost.com/',
    'start': '2026-07-28T00:00:00Z',
    'end': '2026-08-12T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'RevenueCat Shipaton 2026',
    'website': 'https://revenuecat-shipaton-2026.devpost.com/',
    'start': '2026-07-31T00:00:00Z',
    'end': '2026-10-01T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'IncludAI - The Neurodiversity Hackathon',
    'website': 'https://includai-2026.devpost.com/',
    'start': '2026-08-01T00:00:00Z',
    'end': '2026-08-09T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Hacksocial 2026',
    'website': 'https://hacksocial2026.devpost.com/',
    'start': '2026-08-01T00:00:00Z',
    'end': '2026-08-31T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Reverie Hacks 2026',
    'website': 'https://reverie-hacks-2026.devpost.com/',
    'start': '2026-08-02T00:00:00Z',
    'end': '2026-08-17T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Devpost'
    },
    {
    'name': 'Reverie Hacks',
    'website': 'https://reveriehacks.org/',
    'start': '2026-08-02T12:00:00Z',
    'end': '2026-08-17T00:00:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Hack Club'
    },
    {
    'name': 'Paradox',
    'website': 'https://paradox.hackclub.com',
    'start': '2026-08-03T12:00:00Z',
    'end': '2026-08-06T18:00:00Z',
    'city': 'London',
    'state': 'England',
    'country': 'United Kingdom',
    'countryCode': 'GB',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': True,
    'apac': False,
    'source': 'Hack Club'
    },
    {
    'name': 'Horizons Polaris',
    'website': 'https://horizons.hackclub.com/',
    'start': '2026-08-07T16:00:00Z',
    'end': '2026-08-09T16:00:00Z',
    'city': 'Toronto',
    'state': 'Ontario',
    'country': 'Canada',
    'countryCode': 'CA',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': True,
    'apac': False,
    'source': 'Hack Club'
    },
    {
    'name': 'Bay-Valley Hacks',
    'website': 'https://bayvalleyhacks.com/',
    'start': '2026-08-08T08:00:00Z',
    'end': '2026-08-08T22:00:00Z',
    'city': 'Dublin',
    'state': 'California',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Hack Club'
    },
    {
    'name': 'Raingentic Commerce Hackathon NYC',
    'website': 'https://www.eventbrite.com/e/raingentic-commerce-hackathon-nyc-tickets/',
    'start': '2026-08-08T09:00:00Z',
    'end': '2026-08-09T18:00:00Z',
    'city': 'New York',
    'state': 'New York',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Eventbrite'
    },
    {
    'name': 'FireHacks',
    'website': 'https://firehacks.codestarters.org/',
    'start': '2026-08-09T08:00:00Z',
    'end': '2026-08-09T18:00:00Z',
    'city': 'Mountain View',
    'state': 'California',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Hack Club'
    },
    {
    'name': 'Flushing Tech Bi-Weekly Hackathon',
    'website': 'https://www.eventbrite.com/e/flushing-tech-bi-weekly-hackathon-tickets/',
    'start': '2026-08-09T16:00:00Z',
    'end': '2026-08-09T20:00:00Z',
    'city': 'Queens',
    'state': 'New York',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Eventbrite'
    },
    {
    'name': 'Sound and Movement Hackathon',
    'website': 'https://www.eventbrite.com/e/sound-and-movement-hackathon-tickets/',
    'start': '2026-08-10T12:00:00Z',
    'end': '2026-08-10T18:00:00Z',
    'city': 'Brooklyn',
    'state': 'New York',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Eventbrite'
    },
    {
    'name': 'Horizons Equinox',
    'website': 'https://equinox.hackclub.com/',
    'start': '2026-08-14T12:00:00Z',
    'end': '2026-08-16T15:00:00Z',
    'city': 'Cairo',
    'state': 'Cairo',
    'country': 'Egypt',
    'countryCode': 'EG',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': True,
    'apac': False,
    'source': 'Hack Club'
    },
    {
    'name': 'Pixel Forge AI Hackathon',
    'website': 'https://pixelforgehackathons.info/',
    'start': '2026-08-15T04:00:00Z',
    'end': '2026-08-22T20:00:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Hack Club'
    },
    {
    'name': 'Code Arizona',
    'website': 'https://codearizona.codehatch.org/',
    'start': '2026-08-15T09:00:00Z',
    'end': '2026-08-15T19:00:00Z',
    'city': 'Scottsdale',
    'state': 'Arizona',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Hack Club'
    },
    {
    'name': '"Built for NYC": AI Hackathon at NYPL',
    'website': 'https://www.eventbrite.com/e/built-for-nyc-ai-hackathon-at-nypl-tickets/',
    'start': '2026-08-15T11:00:00Z',
    'end': '2026-08-15T18:00:00Z',
    'city': 'New York',
    'state': 'New York',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Eventbrite'
    },
    {
    'name': 'DevNetwork API + Cloud + AI Hackathon',
    'website': 'https://apiworld.co/hackathon/',
    'start': '2026-08-17T10:00:00Z',
    'end': '2026-09-03T16:00:00Z',
    'city': 'Santa Clara',
    'state': 'California',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'DevNetwork'
    },
    {
    'name': '8-Bit Jam',
    'website': 'https://8bitjam.win',
    'start': '2026-08-22T12:00:00Z',
    'end': '2026-08-22T22:00:00Z',
    'city': 'Great Falls',
    'state': 'Virginia',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Hack Club'
    },
    {
    'name': 'Animal Hack',
    'website': 'https://animalhack.org',
    'start': '2026-09-13T15:00:00Z',
    'end': '2026-09-13T17:00:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Hack Club'
    },
    {
    'name': 'Dublin hacx',
    'website': 'https://www.dublinhacx.com/',
    'start': '2026-10-03T09:30:00Z',
    'end': '2026-10-03T22:30:00Z',
    'city': 'San Ramon',
    'state': 'California',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Hack Club'
    },
    {
    'name': 'Banana Hacks',
    'website': 'https://www.bananahacks.tech',
    'start': '2026-10-09T00:00:00Z',
    'end': '2026-10-12T22:00:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Hack Club'
    },
    {
    'name': 'Hyphen-Hacks',
    'website': 'https://www.hyphen-hacks.com/',
    'start': '2026-10-10T09:00:00Z',
    'end': '2026-10-10T23:00:00Z',
    'city': 'San Francisco',
    'state': 'California',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Hack Club'
    },
    {
    'name': 'Global Hack Week: Agents',
    'website': 'https://ghw.mlh.io/',
    'start': '2026-08-07T00:00:00Z',
    'end': '2026-08-13T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'Global Hack Week: Data',
    'website': 'https://ghw.mlh.io/',
    'start': '2026-09-11T00:00:00Z',
    'end': '2026-09-17T23:59:00Z',
    'city': None,
    'state': None,
    'country': None,
    'countryCode': None,
    'virtual': True,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'HackRice 2026',
    'website': 'https://hack.rice.edu/',
    'start': '2026-09-11T00:00:00Z',
    'end': '2026-09-13T23:59:00Z',
    'city': 'Houston',
    'state': 'Texas',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'HackHers @GSU',
    'website': 'https://hackhers.devpost.com/',
    'start': '2026-09-18T00:00:00Z',
    'end': '2026-09-19T23:59:00Z',
    'city': 'Atlanta',
    'state': 'Georgia',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'VTHacks 14',
    'website': 'https://vthacks.com/',
    'start': '2026-09-18T00:00:00Z',
    'end': '2026-09-20T23:59:00Z',
    'city': 'Blacksburg',
    'state': 'Virginia',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'HopHacks',
    'website': 'https://hophacks.com/',
    'start': '2026-09-18T00:00:00Z',
    'end': '2026-09-20T23:59:00Z',
    'city': 'Baltimore',
    'state': 'Maryland',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'SteelHacks XIII',
    'website': 'https://steelhacks.com/',
    'start': '2026-09-19T00:00:00Z',
    'end': '2026-09-20T23:59:00Z',
    'city': 'Pittsburgh',
    'state': 'Pennsylvania',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'HackGT 13',
    'website': 'https://hack.gt/',
    'start': '2026-09-25T00:00:00Z',
    'end': '2026-09-27T23:59:00Z',
    'city': 'Atlanta',
    'state': 'Georgia',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'ShellHacks',
    'website': 'https://shellhacks.net/',
    'start': '2026-09-25T00:00:00Z',
    'end': '2026-09-27T23:59:00Z',
    'city': 'Miami',
    'state': 'Florida',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'DivHacks',
    'website': 'https://divhacks.devpost.com/',
    'start': '2026-09-26T00:00:00Z',
    'end': '2026-09-27T23:59:00Z',
    'city': 'New York',
    'state': 'New York',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'hackUMBC',
    'website': 'https://hackumbc.tech/',
    'start': '2026-09-26T00:00:00Z',
    'end': '2026-09-27T23:59:00Z',
    'city': 'Baltimore',
    'state': 'Maryland',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'BigRed//Hacks 2026',
    'website': 'https://bigredhacks.com/',
    'start': '2026-10-02T00:00:00Z',
    'end': '2026-10-04T23:59:00Z',
    'city': 'Ithaca',
    'state': 'New York',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'Rowdy Hacks',
    'website': 'https://rowdyhacks.com/',
    'start': '2026-10-03T00:00:00Z',
    'end': '2026-10-04T23:59:00Z',
    'city': 'San Antonio',
    'state': 'Texas',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'Hack Dearborn 5: Conjure Reality',
    'website': 'https://hackdearborn.org/',
    'start': '2026-10-03T00:00:00Z',
    'end': '2026-10-04T23:59:00Z',
    'city': 'Dearborn',
    'state': 'Michigan',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'GirlHacks',
    'website': 'https://girlhacks.devpost.com/',
    'start': '2026-10-03T00:00:00Z',
    'end': '2026-10-04T23:59:00Z',
    'city': 'Newark',
    'state': 'New Jersey',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'MHacks',
    'website': 'https://mhacks.org/',
    'start': '2026-10-03T00:00:00Z',
    'end': '2026-10-04T23:59:00Z',
    'city': 'Ann Arbor',
    'state': 'Michigan',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'SBUHacks',
    'website': 'https://sbuhacks.org/',
    'start': '2026-10-09T00:00:00Z',
    'end': '2026-10-11T23:59:00Z',
    'city': 'Stony Brook',
    'state': 'New York',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'HackNC',
    'website': 'https://hacknc.com/',
    'start': '2026-10-09T00:00:00Z',
    'end': '2026-10-11T23:59:00Z',
    'city': 'Chapel Hill',
    'state': 'North Carolina',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'Knight Hacks IX',
    'website': 'https://knighthacks.org/',
    'start': '2026-10-09T00:00:00Z',
    'end': '2026-10-11T23:59:00Z',
    'city': 'Orlando',
    'state': 'Florida',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'CodeRED Orion',
    'website': 'https://codered.devpost.com/',
    'start': '2026-10-10T00:00:00Z',
    'end': '2026-10-11T23:59:00Z',
    'city': 'Houston',
    'state': 'Texas',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'SwampHacks XII',
    'website': 'https://swamphacks.com/',
    'start': '2026-10-16T00:00:00Z',
    'end': '2026-10-18T23:59:00Z',
    'city': 'Gainesville',
    'state': 'Florida',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'HackTX 26',
    'website': 'https://hacktx.com/',
    'start': '2026-10-17T00:00:00Z',
    'end': '2026-10-18T23:59:00Z',
    'city': 'Austin',
    'state': 'Texas',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'HackUTD',
    'website': 'https://hackutd.co/',
    'start': '2026-11-07T00:00:00Z',
    'end': '2026-11-08T23:59:00Z',
    'city': 'Richardson',
    'state': 'Texas',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'MakeCU',
    'website': 'https://makecu.devpost.com/',
    'start': '2026-11-07T00:00:00Z',
    'end': '2026-11-08T23:59:00Z',
    'city': 'New York',
    'state': 'New York',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'HackRPI 2026',
    'website': 'https://hackrpi.com/',
    'start': '2026-11-07T00:00:00Z',
    'end': '2026-11-08T23:59:00Z',
    'city': 'Troy',
    'state': 'New York',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'HackUMass',
    'website': 'https://hackumass.com/',
    'start': '2026-11-13T00:00:00Z',
    'end': '2026-11-15T23:59:00Z',
    'city': 'Amherst',
    'state': 'Massachusetts',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': True,
    'hack_club_event': False,
    'apac': False,
    'source': 'MLH'
    },
    {
    'name': 'AECtech 2026 NYC',
    'website': 'https://www.aectech.nyc/',
    'start': '2026-11-09T15:00:00Z',
    'end': '2026-11-09T21:00:00Z',
    'city': 'New York',
    'state': 'New York',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Eventbrite'
    },
    {
    'name': 'LA Hacks AI Hackathon 2026',
    'website': 'https://lahacks.com/',
    'start': '2026-10-24T00:00:00Z',
    'end': '2026-10-26T23:59:00Z',
    'city': 'Los Angeles',
    'state': 'California',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Hack Club'
    },
    {
    'name': 'Jamaica Tech Bi-Weekly Hackathon',
    'website': 'https://www.eventbrite.com/e/jamaica-tech-bi-weekly-hackathon-tickets/',
    'start': '2026-08-15T15:00:00Z',
    'end': '2026-08-15T19:00:00Z',
    'city': 'Jamaica',
    'state': 'New York',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Eventbrite'
    },
    {
    'name': 'Hackathon for Make-With-Data: Mapping Mental Health',
    'website': 'https://www.eventbrite.com/e/hackathon-for-make-with-data-mapping-mental-health-tickets/',
    'start': '2026-10-21T16:30:00Z',
    'end': '2026-10-21T20:30:00Z',
    'city': 'New York',
    'state': 'New York',
    'country': 'United States',
    'countryCode': 'US',
    'virtual': False,
    'hybrid': False,
    'mlhAssociated': False,
    'hack_club_event': False,
    'apac': False,
    'source': 'Eventbrite'
    }
]

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_GET(self):
        if self.path == "/api/all":
            self.proxy_all()
        else:
            super().do_GET()

    def proxy_all(self):
        all_events = []
        seen = set()

        # Try Hack Club live
        try:
            req = urllib.request.Request(
                "https://hackathons.hackclub.com/api/events/upcoming",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=10, context=ssl_context) as res:
                data = json.loads(res.read().decode())
                for e in data:
                    e["source"] = "Hack Club"
                    key = e.get("name", "").lower().strip()
                    if key and key not in seen:
                        seen.add(key)
                        all_events.append(e)
                print(f"  Hack Club live: {len(data)} events")
        except Exception as e:
            print(f"  Hack Club live failed: {e}")

        # Try Devpost live
        try:
            req = urllib.request.Request(
                "https://devpost.com/api/hackathons",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=10, context=ssl_context) as res:
                data = json.loads(res.read().decode())
                dp_events = self.parse_devpost(data.get("hackathons", []))
                for e in dp_events:
                    key = e.get("name", "").lower().strip()
                    if key and key not in seen:
                        seen.add(key)
                        all_events.append(e)
                print(f"  Devpost live: {len(dp_events)} events")
        except Exception as e:
            print(f"  Devpost live failed: {e}")

        # Fill in missing from fallback
        for e in FALLBACK_DATA:
            key = e.get("name", "").lower().strip()
            if key and key not in seen:
                seen.add(key)
                all_events.append(e)

        print(f"  Total served: {len(all_events)} events")
        self.send_json(all_events)

    def parse_devpost(self, hackathons):
        month_map = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
        events = []
        now = datetime.now()

        for h in hackathons:
            try:
                loc = h.get("displayed_location", {}).get("location", "")
                is_virtual = h.get("displayed_location", {}).get("icon") == "globe" or "online" in loc.lower()

                date_str = h.get("submission_period_dates", "")
                year = 2026
                if "," in date_str:
                    parts = date_str.split(",")
                    date_str = parts[0].strip()
                    year = int(parts[1].strip())

                if " - " in date_str:
                    s, e = date_str.split(" - ", 1)
                    sp = s.strip().split()
                    sm = month_map.get(sp[0].lower()[:3], 1)
                    sd = int(sp[1])
                    ep = e.strip().split()
                    if len(ep) == 1:
                        ed = int(ep[0]); em = sm
                    else:
                        em = month_map.get(ep[0].lower()[:3], sm)
                        ed = int(ep[1])
                    start = datetime(year, sm, sd).isoformat() + "Z"
                    end = datetime(year, em, ed, 23, 59).isoformat() + "Z"
                else:
                    p = date_str.split()
                    m = month_map.get(p[0].lower()[:3], 1)
                    d = int(p[1])
                    dt = datetime(year, m, d).isoformat() + "Z"
                    start = end = dt

                if datetime.fromisoformat(end.replace("Z", "+00:00")).replace(tzinfo=None) < now:
                    continue

                city = state = country = cc = None
                if not is_virtual and loc and "online" not in loc.lower():
                    parts = [p.strip() for p in loc.split(",")]
                    if len(parts) >= 2:
                        city = parts[0]
                        state = parts[1]
                        if len(state) == 2:
                            country = "United States"
                            cc = "US"
                        else:
                            country = state
                            state = None
                    else:
                        city = loc

                events.append({
                    "id": "dp_" + str(h.get("id", "")),
                    "name": h.get("title", ""),
                    "website": h.get("url", ""),
                    "start": start,
                    "end": end,
                    "city": city,
                    "state": state,
                    "country": country,
                    "countryCode": cc,
                    "virtual": is_virtual,
                    "hybrid": False,
                    "mlhAssociated": False,
                    "hack_club_event": False,
                    "apac": False,
                    "source": "Devpost"
                })
            except Exception as e:
                pass

        return events

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\n🚀 Server running at http://localhost:{PORT}")
        print("📡 API endpoint: /api/all")
        print("🛑 Press Ctrl+C to stop\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped.")