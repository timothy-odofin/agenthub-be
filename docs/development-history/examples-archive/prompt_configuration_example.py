#!/usr/bin/env python3
"""
Example: Using Prompt Configuration System

This example demonstrates how to use the centralized prompt configuration
system for managing different types of prompts in AgentHub.
"""

import os
import sys

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from app.core.config.providers.prompt import prompt_config, PromptConfigError, PromptType
from app.core.config.framework.settings import settings


def demonstrate_basic_prompts():
    """Demonstrate basic prompt retrieval."""
    print("=== Basic Prompt Usage ===")
    
    try:
        # Get default chat prompt
        chat_prompt = prompt_config.get_system_prompt("chat.default")
        print(f"Default Chat Prompt:\n{chat_prompt}\n")
        
        # Get technical chat prompt
        technical_prompt = prompt_config.get_system_prompt("chat.technical")
        print(f"Technical Chat Prompt:\n{technical_prompt}\n")
        
        # Get ReAct agent prompt with available tools
        react_prompt = prompt_config.get_system_prompt(
            "agent.react_agent",
            available_tools="search, calculator, code_executor, file_reader"
        )
        print(f"ReAct Agent Prompt:\n{react_prompt}\n")
        
    except PromptConfigError as e:
        print(f"Error getting basic prompts: {e}")


def demonstrate_custom_prompts():
    """Demonstrate custom prompt usage."""
    print("=== Custom Prompt Usage ===")
    
    try:
        # Get code review prompt
        code_review_prompt = prompt_config.get_custom_prompt("code_review")
        print(f"Code Review Prompt:\n{code_review_prompt}\n")
        
        # Get data insights prompt
        data_insights_prompt = prompt_config.get_custom_prompt("data_insights")
        print(f"Data Insights Prompt:\n{data_insights_prompt}\n")
        
    except PromptConfigError as e:
        print(f"Error getting custom prompts: {e}")


def demonstrate_template_prompts():
    """Demonstrate template prompt usage with variables."""
    print("=== Template Prompt Usage ===")
    
    try:
        # Get template variables
        variables = prompt_config.get_template_variables()
        print(f"Available Template Variables: {variables}\n")
        
        # Get personalized greeting with custom variables
        greeting = prompt_config.get_template_prompt(
            "personalized_greeting",
            user_name="Alice Smith",
            company_name="TechCorp",
            current_date="December 7, 2024"
        )
        print(f"Personalized Greeting:\n{greeting}\n")
        
        # Get context-aware response
        context_response = prompt_config.get_template_prompt(
            "context_aware_response",
            environment="production",
            company_name="AgentHub"
        )
        print(f"Context-Aware Response:\n{context_response}\n")
        
    except PromptConfigError as e:
        print(f"Error getting template prompts: {e}")


def demonstrate_environment_prompts():
    """Demonstrate environment-specific prompt usage."""
    print("=== Environment-Specific Prompt Usage ===")
    
    try:
        # Get development environment prompt
        dev_prompt = prompt_config.get_environment_prompt("development", "system.chat.default")
        print(f"Development Environment Prompt:\n{dev_prompt}\n")
        
        # Get production environment prompt (fallback to default)
        prod_prompt = prompt_config.get_environment_prompt("production", "system.chat.default")
        print(f"Production Environment Prompt:\n{prod_prompt}\n")
        
    except PromptConfigError as e:
        print(f"Error getting environment prompts: {e}")


def demonstrate_versioned_prompts():
    """Demonstrate versioned prompt usage."""
    print("=== Versioned Prompt Usage ===")
    
    try:
        # Get prompt from active version
        active_prompt = prompt_config.get_active_version_prompt("chat_default")
        print(f"Active Version Prompt:\n{active_prompt}\n")
        
        # Get prompt for specific user (experimental access)
        experimental_prompt = prompt_config.get_active_version_prompt(
            "chat_default", 
            user_id="admin"
        )
        print(f"Experimental Access Prompt:\n{experimental_prompt}\n")
        
        # Get prompt from specific version
        v1_prompt = prompt_config.get_versioned_prompt("v1_0", "chat_default")
        print(f"Version 1.0 Prompt:\n{v1_prompt}\n")
        
    except PromptConfigError as e:
        print(f"Error getting versioned prompts: {e}")


def demonstrate_prompt_discovery():
    """Demonstrate prompt discovery and listing."""
    print("=== Prompt Discovery ===")
    
    try:
        # List all available prompts
        available_prompts = prompt_config.list_available_prompts()
        
        print("Available System Prompts:")
        for prompt in available_prompts['system']:
            print(f"  - {prompt}")
        
        print("\nAvailable Custom Prompts:")
        for prompt in available_prompts['custom']:
            print(f"  - {prompt}")
        
        print("\nAvailable Templates:")
        for template in available_prompts['templates']:
            print(f"  - {template}")
        
        print("\nAvailable Versions:")
        for version in available_prompts['versions']:
            print(f"  - {version}")
        
        print()
        
    except Exception as e:
        print(f"Error discovering prompts: {e}")


def demonstrate_configuration_info():
    """Demonstrate getting configuration information."""
    print("=== Configuration Information ===")
    
    try:
        # Get default configuration
        default_config = prompt_config.default_config
        print(f"Default Configuration: {default_config}\n")
        
        # Get connection configuration
        connection_config = prompt_config.get_connection_config()
        print(f"Connection Config Type: {connection_config['type']}\n")
        
    except Exception as e:
        print(f"Error getting configuration info: {e}")


def demonstrate_real_world_usage():
    """Demonstrate real-world usage scenarios."""
    print("=== Real-World Usage Scenarios ===")
    
    # Scenario 1: Chat application with user context
    print("Scenario 1: Chat Application")
    try:
        user_context = {
            "user_name": "John Doe",
            "company_name": "TechStartup Inc",
            "environment": "production",
            "user_role": "developer"
        }
        
        # Get appropriate prompt based on user role
        if user_context["user_role"] == "developer":
            prompt = prompt_config.get_system_prompt("chat.technical")
        else:
            prompt = prompt_config.get_system_prompt("chat.business")
        
        print(f"Selected prompt for {user_context['user_role']}: {prompt[:100]}...\n")
        
    except Exception as e:
        print(f"Chat scenario error: {e}")
    
    # Scenario 2: Document processing pipeline
    print("Scenario 2: Document Processing")
    try:
        document_type = "technical_document"
        
        # Get appropriate ingestion prompt
        if document_type == "technical_document":
            prompt = prompt_config.get_system_prompt("ingestion.document_analysis")
        else:
            prompt = prompt_config.get_system_prompt("ingestion.content_summarization")
        
        print(f"Document processing prompt: {prompt[:100]}...\n")
        
    except Exception as e:
        print(f"Document processing scenario error: {e}")
    
    # Scenario 3: A/B testing different prompt versions
    print("Scenario 3: A/B Testing")
    try:
        user_id = "user123"
        
        # Check if user is in experimental group
        if user_id in ["admin", "beta_testers"]:
            prompt = prompt_config.get_active_version_prompt("chat_default", user_id=user_id)
            print(f"Experimental prompt for {user_id}: {prompt[:100]}...")
        else:
            prompt = prompt_config.get_active_version_prompt("chat_default")
            print(f"Standard prompt: {prompt[:100]}...")
        
        print()
        
    except Exception as e:
        print(f"A/B testing scenario error: {e}")


def main():
    """Run all demonstration examples."""
    print("AgentHub Prompt Configuration System Examples")
    print("=" * 50)
    
    try:
        demonstrate_basic_prompts()
        demonstrate_custom_prompts()
        demonstrate_template_prompts()
        demonstrate_environment_prompts()
        demonstrate_versioned_prompts()
        demonstrate_prompt_discovery()
        demonstrate_configuration_info()
        demonstrate_real_world_usage()
        
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"Example execution error: {e}")


if __name__ == "__main__":
    main()
