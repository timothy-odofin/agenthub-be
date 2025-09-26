"""
Example usage of the FileIngestionService with vector store integration.
"""
import asyncio
from pathlib import Path

from src.app.core.constants import DataSourceType, EmbeddingType
from src.app.core.schemas.ingestion_config import DataSourceConfig
from src.app.services.ingestion.file_ingestion_service import FileIngestionService


async def example_file_ingestion():
    """Example of how to use the file ingestion service."""
    
    # Create a sample configuration
    config = DataSourceConfig(
        name="sample_documents",
        type=DataSourceType.FILE,
        sources=[
            "/path/to/your/document.pdf",
            "/path/to/your/text_file.txt",
            # Add more file paths as needed
        ]
    )
    
    # Initialize the file ingestion service
    ingestion_service = FileIngestionService(config)
    
    # You can optionally set a different embedding type
    # ingestion_service.set_embedding_type(EmbeddingType.HUGGINGFACE)
    
    try:
        # Ingest all files configured
        print("Starting file ingestion...")
        success = await ingestion_service.ingest()
        
        if success:
            print("All files processed successfully!")
        else:
            print("Some files failed to process")
        
        # Check individual file status
        status = ingestion_service.get_processed_files_status()
        for file_path, processed in status.items():
            print(f"{file_path}: {'✓' if processed else '✗'}")
            
    except Exception as e:
        print(f"Error during ingestion: {e}")
    finally:
        # Always close connections
        await ingestion_service.close()


async def example_single_file_ingestion():
    """Example of ingesting a single file."""
    
    config = DataSourceConfig(
        name="single_document",
        type=DataSourceType.FILE,
        sources=["/path/to/single/document.pdf"]
    )
    
    ingestion_service = FileIngestionService(config)
    
    try:
        # Ingest just one file
        file_path = "/path/to/single/document.pdf"
        success = await ingestion_service.ingest_single(file_path)
        
        if success:
            print(f"Successfully processed: {file_path}")
        else:
            print(f"Failed to process: {file_path}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await ingestion_service.close()


if __name__ == "__main__":
    # Run the examples
    print("File Ingestion Service Example")
    print("=" * 40)
    
    # Replace with actual file paths in your system
    asyncio.run(example_file_ingestion())
    
    print("\n" + "=" * 40)
    
    asyncio.run(example_single_file_ingestion())
