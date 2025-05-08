from django.shortcuts import render

# Create your views here.


from django.http import JsonResponse

from communication.PubSub.redis import RedisPubSubManager


def publier_message(request):
    manager = RedisPubSubManager()
    manager.connect()
    manager.publish("canal_test", "Message envoyé depuis une vue Django")
    manager.close()
    return JsonResponse({"status": "Message publié"})
