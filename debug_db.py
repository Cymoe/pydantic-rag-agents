import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

def main():
    result = supabase.table('site_pages').select('*').execute()
    print(result)

if __name__ == '__main__':
    main()