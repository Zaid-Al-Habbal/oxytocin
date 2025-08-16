from django.shortcuts import render


# Create your views here.
def dashboard_callback(request, context):
    context.update(
        {
            "cards": [
                {
                    "title": "Card 1",
                    "metric": "100",
                },
                {
                    "title": "Card 2",
                    "metric": "200",
                },
                
            ],
        }
    )

    return context
