from langchain.tools import BaseTool
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from jinja2 import Environment, FileSystemLoader
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
import os
from datetime import datetime
from typing import Optional, Type, Dict
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

class LegalDocumentInput(BaseModel):
    user_issue: str = Field(description="The main issue or concern to be addressed in the legal document")
    insights: str = Field(description="Additional legal insights or context for the document")
    user_name: str = Field(description="Name of the person filing the document")
    location: str = Field(description="Location or jurisdiction where the document is being filed")
    document_type: Optional[str] = Field(description="Type of legal document (PIL, RTI, or Complaint)")
    language: Optional[str] = Field(description="Language code for the document (e.g., 'en', 'hi', 'kn')")

# Language-specific configuration
LANGUAGE_CONFIG = {
    "en": {
        "font": "Times-Roman",
        "headers": {
            "facts": "FACTS OF THE CASE:",
            "legal_basis": "LEGAL BASIS:",
            "prayers": "PRAYERS:",
            "verification": "VERIFICATION:"
        }
    },
    "hi": {
        "font": "Times-Roman",  # Use a font that supports Hindi characters
        "headers": {
            "facts": "मामले के तथ्य:",
            "legal_basis": "कानूनी आधार:",
            "prayers": "प्रार्थनाएँ:",
            "verification": "सत्यापन:"
        }
    },
    "kn": {
        "font": "Times-Roman",  # Use a font that supports Kannada characters
        "headers": {
            "facts": "ಪ್ರಕರಣದ ಅಂಶಗಳು:",
            "legal_basis": "ಕಾನೂನು ಆಧಾರ:",
            "prayers": "ಪ್ರಾರ್ಥನೆಗಳು:",
            "verification": "ಪರಿಶೀಲನೆ:"
        }
    }
}

# Default to English if language is not supported
DEFAULT_LANGUAGE = "en"

class BaseLegalTool(BaseTool):
    name: str
    description: str
    template_file: str
    llm: ChatOpenAI = None
    env: Environment = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = ChatOpenAI(
            temperature=0.3,
            model_name="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.env = Environment(loader=FileSystemLoader("templates"))
        
    def _create_pdf(self, content: str, filename: str, language: str = "en") -> str:
        os.makedirs("generated_pdfs", exist_ok=True)
        filepath = os.path.join("generated_pdfs", filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=LETTER,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get language configuration or default to English
        lang_config = LANGUAGE_CONFIG.get(language, LANGUAGE_CONFIG[DEFAULT_LANGUAGE])
        font_name = lang_config.get("font", "Times-Roman")
        headers = lang_config.get("headers", LANGUAGE_CONFIG[DEFAULT_LANGUAGE]["headers"])
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Justify',
            alignment=TA_JUSTIFY,
            fontName=font_name,
            fontSize=12,
            leading=14,
            spaceBefore=6,
            spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            name='Center',
            alignment=TA_CENTER,
            fontName=font_name,
            fontSize=12,
            leading=14,
            spaceBefore=6,
            spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            name='Header',
            alignment=TA_CENTER,
            fontName=font_name + '-Bold' if '-Bold' not in font_name else font_name,
            fontSize=14,
            leading=16,
            spaceBefore=12,
            spaceAfter=12
        ))
        styles.add(ParagraphStyle(
            name='SubHeader',
            alignment=TA_JUSTIFY,
            fontName=font_name + '-Bold' if '-Bold' not in font_name else font_name,
            fontSize=12,
            leading=14,
            spaceBefore=12,
            spaceAfter=6
        ))
        
        story = []
        lines = content.split('\n')
        
        # Headers in different languages
        facts_header = headers["facts"]
        legal_header = headers["legal_basis"]
        prayers_header = headers["prayers"]
        verification_header = headers["verification"]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if any(line.startswith(header) for header in [facts_header, legal_header, prayers_header, verification_header]):
                story.append(Spacer(1, 12))
                story.append(Paragraph(line, styles['SubHeader']))
            elif line.startswith(('To,', 'प्रति,', 'ಗೆ,')):
                story.append(Paragraph(line, styles['Justify']))
            elif any(line.startswith(prefix) for prefix in ('Subject:', 'विषय:', 'ವಿಷಯ:')):
                story.append(Spacer(1, 12))
                story.append(Paragraph(line, styles['Justify']))
            elif any(line.startswith(prefix) for prefix in ('Respected', 'माननीय', 'ಮಾನ್ಯ')):
                story.append(Spacer(1, 12))
                story.append(Paragraph(line, styles['Justify']))
            elif re.match(r'^\d+\.', line):
                story.append(Paragraph(line, styles['Justify']))
            elif line in ['Petitioner', 'याचिकाकर्ता', 'ಅರ್ಜಿದಾರ', 'Respondents', 'प्रतिवादी', 'ಪ್ರತಿವಾದಿಗಳು']:
                story.append(Paragraph(line, styles['Center']))
            elif any(line.startswith(prefix) for prefix in ('PLACE:', 'स्थान:', 'ಸ್ಥಳ:', 'DATE:', 'दिनांक:', 'ದಿನಾಂಕ:')):
                story.append(Paragraph(line, styles['Justify']))
            else:
                story.append(Paragraph(line, styles['Justify']))
                
        doc.build(story)
        return filepath

    def get_translation_prompt(self, text: str, target_language: str) -> str:
        """Generate a prompt for translating text to the target language"""
        return f"""Translate the following text into {target_language}. 
Keep the same structure, formatting and maintain the formal legal style and terminology:

{text}

Translated text:"""

    def translate_text(self, text: str, language: str) -> str:
        """Translate text to the specified language using LLM"""
        if language == "en":
            return text
            
        language_names = {
            "hi": "Hindi",
            "kn": "Kannada",
            # Add more languages as needed
        }
        
        target_language = language_names.get(language, "English")
        if target_language == "English":
            return text
            
        prompt = self.get_translation_prompt(text, target_language)
        messages = [HumanMessage(content=prompt)]
        translated_text = self.llm(messages).content.strip()
        
        return translated_text

class PILTool(BaseLegalTool):
    name = "PIL"
    description = "Generate a Public Interest Litigation (PIL) document"
    template_file = "pil_template.txt"
    
    def _generate_legal_content(self, user_issue: str, insights: str, language: str = "en") -> tuple[str, str, list]:
        # First generate the facts of the case
        facts_prompt = (
            f"You are a senior advocate drafting a PIL petition. Given the following issue, write a concise and relevant FACTS OF THE CASE section.\n"
            f"Issue: {user_issue}\n"
            f"Additional Context: {insights}\n"
            f"Generate 2-3 key points that are most relevant to the case. Each point should be:\n"
            f"- Clear and concise\n"
            f"- Include specific dates and facts\n"
            f"- Focus on the most critical aspects\n"
            f"- Be properly formatted as numbered points\n"
            f"- DO NOT use any markdown formatting or special characters\n"
            f"Format the response as:\n"
            f"1. [First key point]\n"
            f"2. [Second key point]\n"
            f"3. [Third key point]"
        )
        facts_messages = [HumanMessage(content=facts_prompt)]
        facts_response = self.llm(facts_messages).content
        
        # Clean up the facts response
        facts_lines = [line.strip() for line in facts_response.split('\n') if line.strip()]
        facts_lines = [re.sub(r'\*\*|\*', '', line) for line in facts_lines]
        issue_summary = '\n'.join(facts_lines)
        
        # Now generate the legal basis
        legal_prompt = (
            f"You are a senior advocate drafting a PIL petition. Given the following issue, write a concise and relevant LEGAL BASIS section.\n"
            f"Issue: {user_issue}\n"
            f"Additional Context: {insights}\n"
            f"Generate 3-4 key legal points that are most relevant to the case. Each point should:\n"
            f"- Cite specific constitutional provisions, laws, or precedents\n"
            f"- Explain how they apply to the case\n"
            f"- Be properly formatted as numbered points\n"
            f"- DO NOT use any markdown formatting or special characters\n"
            f"Format the response as:\n"
            f"1. [First legal point with citation]\n"
            f"2. [Second legal point with citation]\n"
            f"3. [Third legal point with citation]\n"
            f"4. [Fourth legal point with citation]"
        )
        legal_messages = [HumanMessage(content=legal_prompt)]
        legal_response = self.llm(legal_messages).content
        
        # Clean up the legal response
        legal_lines = [line.strip() for line in legal_response.split('\n') if line.strip()]
        legal_lines = [re.sub(r'\*\*|\*', '', line) for line in legal_lines]
        legal_insights = '\n'.join(legal_lines)
        
        # Finally generate the prayers
        prayers_prompt = (
            f"You are a senior advocate drafting a PIL petition. Given the following issue, write 1-2 specific and relevant PRAYERS.\n"
            f"Issue: {user_issue}\n"
            f"Additional Context: {insights}\n"
            f"Generate 1-2 specific prayers that:\n"
            f"- Are directly related to the issue\n"
            f"- Request concrete actions from the authorities\n"
            f"- Include specific timeframes where appropriate\n"
            f"- Be properly formatted as numbered points\n"
            f"- Be concise and to the point\n"
            f"- DO NOT use any markdown formatting or special characters\n"
            f"Format the response as:\n"
            f"1. [First prayer]\n"
            f"2. [Second prayer]"
        )
        prayers_messages = [HumanMessage(content=prayers_prompt)]
        prayers_response = self.llm(prayers_messages).content
        
        # Clean up and format the prayers
        prayers = [prayer.strip() for prayer in prayers_response.split('\n') if prayer.strip()]
        prayers = [re.sub(r'\*\*|\*', '', prayer) for prayer in prayers]
        prayers = [re.sub(r'^\d+\.\s*', '', prayer) for prayer in prayers]
        formatted_prayers = [f"{i+1}. {prayer}" for i, prayer in enumerate(prayers)]
        
        return issue_summary, legal_insights, formatted_prayers
    
    def _run(self, user_issue: str, insights: str, user_name: str, location: str, contact_number: str = None, language: str = "en") -> str:
        issue_summary, legal_insights, prayers = self._generate_legal_content(user_issue, insights, language)
        current_date = datetime.now()
        
        # Extract city and state from location
        location_parts = location.split(',')
        city = location_parts[0].strip()
        state = location_parts[1].strip() if len(location_parts) > 1 else location
        
        # Generate dynamic respondents based on location
        respondents = [
            f"State of {state}",
            f"{state} Pollution Control Committee",
            "Ministry of Environment, Forest and Climate Change",
            "Central Pollution Control Board",
            f"Municipal Corporation of {city}",
            f"{city} Development Authority"
        ]
        
        # Get language-specific headers
        lang_config = LANGUAGE_CONFIG.get(language, LANGUAGE_CONFIG[DEFAULT_LANGUAGE])
        headers = lang_config.get("headers", LANGUAGE_CONFIG[DEFAULT_LANGUAGE]["headers"])
        
        template = self.env.get_template(self.template_file)
        content = template.render(
            user_name=user_name,
            user_address=city,
            location=state,
            issue_summary=issue_summary,
            legal_insights=legal_insights,
            date=current_date.strftime("%d %B, %Y"),
            year=current_date.year,
            month=current_date.strftime("%B"),
            respondents=respondents,
            petition_purpose="environmental protection and public health",
            issue_description="environmental pollution and public health hazards",
            prayers=prayers,
            contact_details=f"Contact: {contact_number or '[Contact Number]'}\nAddress: {city}",
            headers=headers
        )
        
        # Translate the content if not in English
        if language != "en":
            content = self.translate_text(content, language)
            
        filename = f"PIL_{user_name.replace(' ', '_')}_{language}.pdf"
        return self._create_pdf(content, filename, language)

class RTITool(BaseLegalTool):
    name = "RTI"
    description = "Generate a Right to Information (RTI) application"
    template_file = "rti_template.txt"
    
    def _generate_legal_content(self, user_issue: str, insights: str, language: str = "en") -> tuple[str, str, str, list]:
        # Generate subject line
        subject_prompt = (
            f"You are drafting an RTI application. Given the following issue, write a concise subject line.\n"
            f"Issue: {user_issue}\n"
            f"Additional Context: {insights}\n"
            f"The subject line should be clear, specific, and indicate what information is being sought.\n"
            f"It should start with 'RTI Application for...'\n"
            f"Format: Just provide the subject line, nothing else."
        )
        subject_messages = [HumanMessage(content=subject_prompt)]
        subject = self.llm(subject_messages).content.strip()
        
        # Generate introduction
        intro_prompt = (
            f"You are drafting an RTI application. Given the following issue, write a concise introduction paragraph.\n"
            f"Issue: {user_issue}\n"
            f"Additional Context: {insights}\n"
            f"The introduction should establish your identity, the basis of your right to information, and briefly introduce the issue.\n"
            f"Format: A single paragraph of 3-5 sentences."
        )
        intro_messages = [HumanMessage(content=intro_prompt)]
        introduction = self.llm(intro_messages).content.strip()
        
        # Generate information requested
        info_prompt = (
            f"You are drafting an RTI application. Given the following issue, write 3-5 specific information requests.\n"
            f"Issue: {user_issue}\n"
            f"Additional Context: {insights}\n"
            f"Each request should:\n"
            f"- Be specific and precise\n"
            f"- Focus on information the authority is likely to have\n"
            f"- Include timeframes where relevant\n"
            f"- Be properly formatted as numbered points\n"
            f"Format the response as:\n"
            f"1. [First information request]\n"
            f"2. [Second information request]\n"
            f"3. [Third information request]\n"
            f"4. [Fourth information request]\n"
            f"5. [Fifth information request]"
        )
        info_messages = [HumanMessage(content=info_prompt)]
        info_response = self.llm(info_messages).content
        
        # Clean up and format the information requests
        info_requests = [req.strip() for req in info_response.split('\n') if req.strip()]
        info_requests = [re.sub(r'\*\*|\*', '', req) for req in info_requests]
        
        # Generate closing
        closing_prompt = (
            f"You are drafting an RTI application. Given the following issue, write a concluding paragraph.\n"
            f"Issue: {user_issue}\n"
            f"Additional Context: {insights}\n"
            f"The closing should:\n"
            f"- Express willingness to pay necessary fees\n"
            f"- Request a timely response\n"
            f"- Express gratitude\n"
            f"Format: A single paragraph of 2-3 sentences."
        )
        closing_messages = [HumanMessage(content=closing_prompt)]
        closing = self.llm(closing_messages).content.strip()
        
        return subject, introduction, closing, info_requests
    
    def _run(self, user_issue: str, insights: str, user_name: str, location: str, contact_number: str = None, language: str = "en") -> str:
        subject, introduction, closing, info_requests = self._generate_legal_content(user_issue, insights, language)
        current_date = datetime.now()
        
        # Extract city and state from location
        location_parts = location.split(',')
        city = location_parts[0].strip()
        state = location_parts[-1].strip() if len(location_parts) > 1 else location
        
        # Determine appropriate authority based on issue
        authority_prompt = (
            f"Given the following RTI application details, determine the most appropriate government authority to address this request:\n\n"
            f"Subject: {subject}\n"
            f"Issue: {user_issue}\n\n"
            f"Respond with just the name of the most appropriate government department/authority at the central, state, or local level."
        )
        authority_messages = [HumanMessage(content=authority_prompt)]
        authority = self.llm(authority_messages).content.strip()
        
        template = self.env.get_template(self.template_file)
        content = template.render(
            user_name=user_name,
            user_address=f"{city}, {state}",
            authority=authority,
            subject=subject,
            introduction=introduction,
            info_requests=info_requests,
            closing=closing,
            date=current_date.strftime("%d %B, %Y"),
            contact_details=f"Contact: {contact_number or '[Contact Number]'}"
        )
        
        # Translate the content if not in English
        if language != "en":
            content = self.translate_text(content, language)
            
        filename = f"RTI_{user_name.replace(' ', '_')}_{language}.pdf"
        return self._create_pdf(content, filename, language)

class ComplaintTool(BaseLegalTool):
    name = "Complaint"
    description = "Generate a formal complaint document"
    template_file = "complaint_template.txt"
    
    def _generate_legal_content(self, user_issue: str, insights: str, language: str = "en") -> tuple[str, str, str, str, str, list, list]:
        # First generate the facts of the case
        facts_prompt = (
            f"You are drafting a formal consumer complaint. Given the following issue, write a concise and relevant FACTS OF THE CASE section.\n"
            f"Issue: {user_issue}\n"
            f"Additional Context: {insights}\n"
            f"Generate 2-3 key points that are most relevant to the complaint. Each point should be:\n"
            f"- Clear and concise\n"
            f"- Include specific dates and facts\n"
            f"- Focus on the most critical aspects\n"
            f"- Be properly formatted as numbered points\n"
            f"Format the response as:\n"
            f"1. [First key point]\n"
            f"2. [Second key point]\n"
            f"3. [Third key point]"
        )
        facts_messages = [HumanMessage(content=facts_prompt)]
        facts_response = self.llm(facts_messages).content
        
        # Clean up the facts response
        facts_lines = [line.strip() for line in facts_response.split('\n') if line.strip()]
        facts_lines = [re.sub(r'\*\*|\*', '', line) for line in facts_lines]
        issue_summary = '\n'.join(facts_lines)
        
        # Generate subject line
        subject_prompt = (
            f"You are drafting a formal consumer complaint. Given the following issue, write a concise subject line.\n"
            f"Issue: {user_issue}\n"
            f"Additional Context: {insights}\n"
            f"The subject line should be clear, specific, and indicate the nature of the complaint.\n"
            f"Format: Just provide the subject line, nothing else."
        )
        subject_messages = [HumanMessage(content=subject_prompt)]
        subject = self.llm(subject_messages).content.strip()
        
        # Generate introduction
        intro_prompt = (
            f"You are drafting a formal consumer complaint. Given the following issue, write a concise introduction paragraph.\n"
            f"Issue: {user_issue}\n"
            f"Additional Context: {insights}\n"
            f"The introduction should establish your identity and briefly introduce the issue.\n"
            f"Format: A single paragraph of 3-5 sentences."
        )
        intro_messages = [HumanMessage(content=intro_prompt)]
        introduction = self.llm(intro_messages).content.strip()
        
        # Generate closing
        closing_prompt = (
            f"You are drafting a formal consumer complaint. Given the following issue, write a concluding paragraph.\n"
            f"Issue: {user_issue}\n"
            f"Additional Context: {insights}\n"
            f"The closing should:\n"
            f"- Express what outcome you desire\n"
            f"- Request a timely response\n"
            f"- Express gratitude\n"
            f"Format: A single paragraph of 2-3 sentences."
        )
        closing_messages = [HumanMessage(content=closing_prompt)]
        closing = self.llm(closing_messages).content.strip()
        
        # Generate grievances
        grievances_prompt = (
            f"You are drafting a formal consumer complaint. Given the following issue, write 2-3 specific grievances.\n"
            f"Issue: {user_issue}\n"
            f"Additional Context: {insights}\n"
            f"Each grievance should:\n"
            f"- Be specific and precise\n"
            f"- Focus on a distinct aspect of the complaint\n"
            f"- Be properly formatted as numbered points\n"
            f"Format the response as:\n"
            f"1. [First grievance]\n"
            f"2. [Second grievance]\n"
            f"3. [Third grievance]"
        )
        grievances_messages = [HumanMessage(content=grievances_prompt)]
        grievances_response = self.llm(grievances_messages).content
        
        # Clean up and format the grievances
        grievances = [req.strip() for req in grievances_response.split('\n') if req.strip()]
        grievances = [re.sub(r'\*\*|\*', '', req) for req in grievances]
        
        # Generate demands/relief sought
        demands_prompt = (
            f"You are drafting a formal consumer complaint. Given the following issue, write 2-3 specific demands or relief sought.\n"
            f"Issue: {user_issue}\n"
            f"Additional Context: {insights}\n"
            f"Each demand should:\n"
            f"- Be specific and reasonable\n"
            f"- Clearly state what you want the recipient to do\n"
            f"- Include timeframes where appropriate\n"
            f"- Be properly formatted as numbered points\n"
            f"Format the response as:\n"
            f"1. [First demand]\n"
            f"2. [Second demand]\n"
            f"3. [Third demand]"
        )
        demands_messages = [HumanMessage(content=demands_prompt)]
        demands_response = self.llm(demands_messages).content
        
        # Clean up and format the demands
        demands = [req.strip() for req in demands_response.split('\n') if req.strip()]
        demands = [re.sub(r'\*\*|\*', '', req) for req in demands]
        
        return subject, introduction, issue_summary, closing, authority, grievances, demands
    
    def _run(self, user_issue: str, insights: str, user_name: str, location: str, contact_number: str = None, language: str = "en") -> str:
        # Determine appropriate authority based on issue
        authority_prompt = (
            f"Given the following consumer complaint details, determine the most appropriate authority to address this complaint:\n\n"
            f"Issue: {user_issue}\n"
            f"Additional Context: {insights}\n\n"
            f"Respond with just the name and designation of the most appropriate authority (e.g., 'The District Consumer Disputes Redressal Commission, [City]')."
        )
        authority_messages = [HumanMessage(content=authority_prompt)]
        authority = self.llm(authority_messages).content.strip()

        subject, introduction, issue_summary, closing, _, grievances, demands = self._generate_legal_content(user_issue, insights, language)
        current_date = datetime.now()
        
        # Extract city and state from location
        location_parts = location.split(',')
        city = location_parts[0].strip()
        state = location_parts[-1].strip() if len(location_parts) > 1 else location
        
        template = self.env.get_template(self.template_file)
        content = template.render(
            user_name=user_name,
            user_address=f"{city}, {state}",
            authority=authority,
            subject=subject,
            introduction=introduction,
            issue_summary=issue_summary,
            grievances=grievances,
            demands=demands,
            closing=closing,
            date=current_date.strftime("%d %B, %Y"),
            contact_details=f"Contact: {contact_number or '[Contact Number]'}"
        )
        
        # Translate the content if not in English
        if language != "en":
            content = self.translate_text(content, language)
            
        filename = f"Complaint_{user_name.replace(' ', '_')}_{language}.pdf"
        return self._create_pdf(content, filename, language) 