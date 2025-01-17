from django.http import JsonResponse, HttpResponse
from movementditection.models.pushups import PushupsModel
import json
from django.views.decorators.csrf import csrf_exempt


pushups_model = PushupsModel()

@csrf_exempt
def pushup_count_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            frame_data = data.get('frame')
            if not frame_data:
                return JsonResponse({'error': 'No frame provided'}, status=400)
            
            result = pushups_model.process_frame(frame_data)
            return JsonResponse(result)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return HttpResponse("Only POST requests are allowed on this route.", status=405)
