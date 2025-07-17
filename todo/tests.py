from django.test import TestCase, Client
from django.utils import timezone
from datetime import datetime
from todo.models import Task


# Create your tests here.


class SampleTestCase(TestCase):
    def test_sample1(self):
        self.assertEqual(1 + 2, 3)


class TaskModelTestCase(TestCase):
    def test_create_task1(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        task = Task(title="task1", due_at=due)
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, "task1")
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, due)

    def test_create_task2(self):
        task = Task(title="task2")
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, "task2")
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, None)

    def test_is_overdue_future(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 6, 30, 0, 0, 0))
        task = Task(title="task1", due_at=due)
        task.save()

        self.assertFalse(task.is_overdue(current))

    def test_is_overduez_past(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title="task1", due_at=due)
        task.save()

        self.assertTrue(task.is_overdue(current))

    def test_is_overduez_none(self):
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title="task1")
        task.save()

        self.assertFalse(task.is_overdue(current))


class TodoViewTestCase(TestCase):
    def test_index_get(self):
        client = Client()
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(len(response.context["tasks"]), 0)

    def test_index_post(self):
        client = Client()
        data = {"title": "Test Task", "due_at": "2024-06-30 23:59:59"}
        response = client.post("/", data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(len(response.context["tasks"]), 1)

    def test_index_get_order_post(self):
        task1 = Task(title="task1", due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title="task2", due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()
        client = Client()
        response = client.get("/?order=post")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(response.context["tasks"][0], task2)
        self.assertEqual(response.context["tasks"][1], task1)

    def test_index_get_order_due(self):
        task1 = Task(title="task1", due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title="task2", due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()
        client = Client()
        response = client.get("/?order=due")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(response.context["tasks"][0], task1)
        self.assertEqual(response.context["tasks"][1], task2)

    def test_detail_get_success(self):
        task = Task(title="task1", due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client=Client()
        response=client.get("/{}/".format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/detail.html")
        self.assertEqual(response.context["task"], task)

    def test_detail_get_fail(self):
        client=Client()
        response=client.get("/1/")

        self.assertEqual(response.status_code, 404)

class TaskUpdateViewTestCase(TestCase):
    def setUp(self):
        self.task = Task.objects.create(
            title="Old Title",
            due_at=timezone.make_aware(datetime(2024, 7, 1))
        )
        self.client = Client()

    def test_update_get(self):
        """
        GETリクエストで編集画面が表示されるか
        """
        response = self.client.get(f"/update/{self.task.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/edit.html")
        self.assertEqual(response.context["task"], self.task)

    def test_update_post(self):
        """
        POSTリクエストでタイトル・締切が変更されるか
        """
        data = {
            "title": "Updated Title",
            "due_at": "2024-07-15 12:00:00"
        }
        response = self.client.post(f"/update/{self.task.pk}/", data, follow=True)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Updated Title")
        self.assertEqual(self.task.due_at, timezone.make_aware(datetime(2024, 7, 15, 12, 0, 0)))
        # 正しくリダイレクトされ detail.html を返すか
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/detail.html")
        self.assertEqual(response.context["task"], self.task)
    
    def test_update_post_not_found(self):
        """
        存在しないタスクには404 (POST)
        """
        response = self.client.post("/update/9999/", {"title": "nope", "due_at": "2024-08-01 00:00:00"})
        self.assertEqual(response.status_code, 404)
