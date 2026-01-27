import sys
import os
import argparse

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', required=True)
    parser.add_argument('--email', required=True)
    parser.add_argument('--password', required=True)
    args = parser.parse_args(argv)

    # Ensure project root is on path and Django settings are set
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neonatology_project.settings')
    import django
    django.setup()

    from django.contrib.auth import get_user_model
    User = get_user_model()

    if User.objects.filter(username=args.username).exists():
        print(f"User '{args.username}' already exists; updating password and email.")
        user = User.objects.get(username=args.username)
        user.email = args.email
        user.set_password(args.password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print('Updated existing superuser')
    else:
        print(f"Creating superuser {args.username}")
        User.objects.create_superuser(args.username, args.email, args.password)
        print('Superuser created')

if __name__ == '__main__':
    main()
