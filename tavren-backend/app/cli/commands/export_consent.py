import asyncio
import json
import os
import typer
from typing import Optional, List
from datetime import datetime

from app.database import get_db_sync, AsyncSession
from app.utils.consent_export import get_consent_export
from app.services.user import get_user_service

app = typer.Typer(help="Commands for managing consent exports")

@app.command()
def export_user(
    user_id: str = typer.Argument(..., help="User ID to export data for"),
    output_dir: str = typer.Option(None, help="Directory to save export files (default: ./exports)"),
    include_pet_queries: bool = typer.Option(False, help="Include PET query logs in export"),
):
    """Generate a verifiable export package for a specific user."""
    asyncio.run(_export_user(user_id, output_dir, include_pet_queries))
    
async def _export_user(user_id: str, output_dir: Optional[str], include_pet_queries: bool):
    async with get_db_sync() as db:
        # Validate user exists
        user_service = await get_user_service(db)
        user = await user_service.get_user_by_id(user_id)
        if not user:
            typer.echo(f"Error: User with ID {user_id} not found")
            raise typer.Exit(code=1)
        
        # Create export
        export_service = await get_consent_export(db)
        try:
            export_data = await export_service.generate_export_package(
                user_id=user_id,
                include_pet_queries=include_pet_queries,
                sign_export=True
            )
            
            # Save to file
            file_path = await export_service.save_export_file(export_data, output_dir)
            
            typer.echo(f"Export created successfully and saved to {file_path}")
            typer.echo(f"Export hash: {export_data.get('hash', 'N/A')}")
            
        except Exception as e:
            typer.echo(f"Error generating export: {str(e)}")
            raise typer.Exit(code=1)

@app.command()
def batch_export(
    user_file: str = typer.Argument(..., help="Path to file containing user IDs, one per line"),
    output_dir: str = typer.Option(None, help="Directory to save export files"),
    include_pet_queries: bool = typer.Option(False, help="Include PET query logs in export"),
):
    """Generate export packages for multiple users from a file."""
    # Check if file exists
    if not os.path.exists(user_file):
        typer.echo(f"Error: File {user_file} not found")
        raise typer.Exit(code=1)
    
    # Read user IDs from file
    with open(user_file, 'r') as f:
        user_ids = [line.strip() for line in f if line.strip()]
    
    if not user_ids:
        typer.echo("Error: No user IDs found in file")
        raise typer.Exit(code=1)
    
    typer.echo(f"Found {len(user_ids)} user IDs in file. Starting export...")
    
    # Process each user
    success_count = 0
    failed_users = []
    
    for user_id in typer.track(user_ids, description="Exporting user data"):
        try:
            asyncio.run(_export_user(user_id, output_dir, include_pet_queries))
            success_count += 1
        except Exception:
            failed_users.append(user_id)
    
    # Print summary
    typer.echo(f"\nExport complete. Successfully exported {success_count} of {len(user_ids)} users.")
    if failed_users:
        typer.echo(f"Failed to export {len(failed_users)} users: {', '.join(failed_users[:5])}" + 
                  (f" and {len(failed_users) - 5} more" if len(failed_users) > 5 else ""))

@app.command()
def verify_export(
    export_file: str = typer.Argument(..., help="Path to export file to verify"),
):
    """Verify the integrity of an export file."""
    if not os.path.exists(export_file):
        typer.echo(f"Error: File {export_file} not found")
        raise typer.Exit(code=1)
    
    try:
        # Load export data
        with open(export_file, 'r') as f:
            export_data = json.load(f)
        
        # Check required fields
        required_fields = ['export_id', 'export_timestamp', 'user_id', 'hash']
        missing_fields = [field for field in required_fields if field not in export_data]
        
        if missing_fields:
            typer.echo(f"Error: Export file missing required fields: {', '.join(missing_fields)}")
            raise typer.Exit(code=1)
        
        # Get stored hash
        stored_hash = export_data.pop('hash', None)
        if not stored_hash:
            typer.echo("Error: Export file does not contain a hash")
            raise typer.Exit(code=1)
        
        # Recalculate hash
        asyncio.run(_verify_hash(export_data, stored_hash))
        
    except json.JSONDecodeError:
        typer.echo("Error: Invalid JSON format in export file")
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error verifying export: {str(e)}")
        raise typer.Exit(code=1)

async def _verify_hash(export_data: dict, stored_hash: str):
    async with get_db_sync() as db:
        export_service = await get_consent_export(db)
        calculated_hash = await export_service.calculate_export_hash(export_data)
        
        if calculated_hash == stored_hash:
            typer.echo("✅ Export verification successful! Hash matches.")
            return True
        else:
            typer.echo("❌ Export verification failed! Hash does not match.")
            typer.echo(f"Stored hash: {stored_hash}")
            typer.echo(f"Calculated hash: {calculated_hash}")
            raise typer.Exit(code=1)

if __name__ == "__main__":
    app() 