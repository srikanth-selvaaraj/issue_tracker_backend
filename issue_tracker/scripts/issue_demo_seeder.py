import traceback
from ..models import User, Project, Issue
from faker import Faker

fake = Faker()

def run():
    try:
        user = User.objects.get(pk=10)
        project = Project.objects.get(pk=10)

        issues = []
        for i in range(0, 30):
            title = fake.name()
            description = fake.address()

            issues.append(Issue(owner=user, project=project, title=title, description=description))

        Issue.objects.bulk_create(issues)

    except Exception as e:
        print(e)
        traceback.print_exc()
