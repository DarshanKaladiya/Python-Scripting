import json

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import OfflineAction, Terminal


@csrf_exempt
@require_POST
def offline_actions(request):
    payload = json.loads(request.body.decode("utf-8") or "{}")
    terminal, _ = Terminal.objects.get_or_create(
        code=payload.get("terminal_code", "default-terminal"),
        defaults={"name": payload.get("terminal_name", "Default Terminal")},
    )
    action, created = OfflineAction.objects.get_or_create(
        idempotency_key=payload["idempotency_key"],
        defaults={
            "terminal": terminal,
            "action_type": payload.get("action_type", "unknown"),
            "payload": payload.get("payload", {}),
            "status": OfflineAction.Status.PROCESSED,
            "synced_at": timezone.now(),
        },
    )
    return JsonResponse({"created": created, "status": action.status, "offline_action_id": action.id})


@require_GET
def pending_status(request):
    terminal_code = request.GET.get("terminal_code")
    terminal = Terminal.objects.filter(code=terminal_code).first()
    pending = OfflineAction.objects.filter(terminal=terminal, status=OfflineAction.Status.PENDING).count() if terminal else 0
    return JsonResponse({"pending_actions": pending})

# Create your views here.
