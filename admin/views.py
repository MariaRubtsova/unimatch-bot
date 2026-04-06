import os
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

from db.models import User, Program, UserDeadline, ChecklistItem, DocumentTemplate


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        if username == os.getenv("ADMIN_USERNAME", "admin") and \
           password == os.getenv("ADMIN_PASSWORD", "changeme"):
            request.session.update({"admin": "authenticated"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request):
        if request.session.get("admin") == "authenticated":
            return True
        return RedirectResponse(request.url_for("admin:login"), status_code=302)


class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-users"
    column_list = [User.user_id, User.username, User.first_name, User.created_at, User.last_active]
    column_searchable_list = [User.username, User.first_name]
    can_create = False
    can_delete = False


class ProgramAdmin(ModelView, model=Program):
    name = "Программа"
    name_plural = "Вузы и программы"
    icon = "fa-solid fa-graduation-cap"
    column_list = [
        Program.id, Program.university_name, Program.program_name,
        Program.country, Program.field, Program.degree_type,
        Program.min_gpa, Program.min_ielts, Program.tuition_year,
        Program.deadline, Program.is_active,
    ]
    column_searchable_list = [Program.university_name, Program.program_name, Program.country]
    column_sortable_list = [Program.deadline, Program.tuition_year, Program.min_gpa]
    column_filters = [Program.country, Program.field, Program.degree_type, Program.is_active]
    # Exclude embedding from edit form (handled separately)
    form_excluded_columns = [Program.embedding, Program.created_at, Program.updated_at]


class UserDeadlineAdmin(ModelView, model=UserDeadline):
    name = "Дедлайн"
    name_plural = "Дедлайны пользователей"
    icon = "fa-solid fa-calendar"
    column_list = [
        UserDeadline.id, UserDeadline.user_id, UserDeadline.program_id,
        UserDeadline.deadline, UserDeadline.notified_30, UserDeadline.notified_7, UserDeadline.notified_1,
    ]
    can_create = False


class ChecklistItemAdmin(ModelView, model=ChecklistItem):
    name = "Чеклист"
    name_plural = "Чеклисты"
    icon = "fa-solid fa-list-check"
    column_list = [
        ChecklistItem.id, ChecklistItem.user_id, ChecklistItem.program_id,
        ChecklistItem.item_name, ChecklistItem.is_done,
    ]
    can_create = False


class DocumentTemplateAdmin(ModelView, model=DocumentTemplate):
    name = "Шаблон документа"
    name_plural = "Шаблоны документов"
    icon = "fa-solid fa-file"
    column_list = [
        DocumentTemplate.id, DocumentTemplate.degree_type,
        DocumentTemplate.item_name, DocumentTemplate.hint, DocumentTemplate.order_index,
    ]


def setup_admin(app, engine):
    authentication_backend = AdminAuth(secret_key=os.getenv("SECRET_KEY", "change_me"))
    admin = Admin(app, engine, authentication_backend=authentication_backend)
    admin.add_view(UserAdmin)
    admin.add_view(ProgramAdmin)
    admin.add_view(UserDeadlineAdmin)
    admin.add_view(ChecklistItemAdmin)
    admin.add_view(DocumentTemplateAdmin)
    return admin
