from django.shortcuts import render, Http404, HttpResponseRedirect, reverse, get_object_or_404, HttpResponse
from django.conf import settings
import stripe
from django.contrib.auth.decorators import login_required
from payments.models import StripeCard
from django.contrib.sites.models import Site
from hotel.models import Room

# Create your views here.


@login_required
def view_cards(request):

    cards_detail = stripe.Customer.list_sources(
        request.user.stripe_data.customer_id,
        api_key=settings.STRIPE_SECRET_KEY
    )

    return render(request, 'payments/view_cards.html', {
        'cards': cards_detail['data']
    })


@login_required
def add_card(request):

    if request.method == 'GET':
        return render(request, 'payments/add_card.html', {'stripe_key': settings.STRIPE_PUBLIC_KEY})
        # we make request from the web page

    else:
        if 'stripeToken' in request.POST:
            stripe_token = request.POST['stripeToken']
            card = stripe.Customer.create_source(
                request.user.stripe_data.customer_id,
                source=stripe_token,
                api_key=settings.STRIPE_SECRET_KEY  # because we make request from the app
            )

            StripeCard(customer=request.user.stripe_data, card_id=card['id']).save()

            return HttpResponseRedirect(reverse('payments:view_cards'))

        raise Http404


@login_required()
def delete_card(request, card_id):
    # if request.method == 'POST':
    if request.POST:
        stripe_customer = request.user.stripe_data

        card = get_object_or_404(StripeCard, customer=stripe_customer, card_id=card_id)

        stripe.Customer.delete_source(
            stripe_customer.customer_id,
            card_id,
            api_key=settings.STRIPE_SECRET_KEY
        )

        card.delete()

        return HttpResponseRedirect(reverse('payments:view_cards'))

    raise Http404


@login_required
def handle_payment(request, room_id):

    print("***********************")
    print(room_id)

    room_pay = get_object_or_404(Room, pk=room_id)
    price_pay = int(room_pay.price * 100)

    # return HttpResponse("OK")

    stripe_customer = request.user.stripe_data
    host = Site.objects.get_current().domain
    payment_process_url = f"{host}{reverse('payments:process')}"
    payment_intent = stripe.PaymentIntent.create(
        amount=price_pay,
        currency='ron',
        customer=stripe_customer.customer_id,
        payment_method=stripe_customer.cards.first().card_id,
        confirm=True,
        return_url=payment_process_url,
        api_key=settings.STRIPE_SECRET_KEY
    )

    if payment_intent['next_action']:
        return HttpResponseRedirect(payment_intent['next_action']['redirect_to_url']['url'])

    return HttpResponseRedirect(reverse('payments:process'))


@login_required
def handle_payment_process(request):
    payment_intent_id = request.GET.get('payment_intent', None)

    if payment_intent_id:
        payment_intent = stripe.PaymentIntent.retrieve(
            payment_intent_id,
            api_key=settings.STRIPE_SECRET_KEY
        )

        if payment_intent['last_payment_error']:
            stripe.PaymentIntent.cancel(
                payment_intent_id,
                api_key=settings.STRIPE_SECRET_KEY
            )
            return HttpResponseRedirect(reverse('payment:failed'))

    return HttpResponseRedirect(reverse('payments:done'))


@login_required
def payment_done(request):

    return render(request, "payments/payment_done.html")


@login_required()
def payment_failed(request):
    return HttpResponse('Payment failed!')

