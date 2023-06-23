from django.contrib import admin

from challenge.models import GroupSubmit


class MLSubmission(GroupSubmit):
    class Meta:
        proxy = True
        verbose_name = "ML Submissions"


@admin.register(MLSubmission)
class MLSubmissionAdmin(admin.ModelAdmin):
    fields = ["group", "file", "score", "team_members"]
    readonly_fields = ["group", "file", "team_members"]
    list_display = ["id", "group", "score"]
    actions_on_top = []

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return MLSubmission.objects.all().filter(phase__challenge__name="ml")

    @admin.display(description="Team Members")
    def team_members(self, instance: MLSubmission):
        return "\n".join(instance.group.challengeuser_set.values_list("full_name", flat=True))
