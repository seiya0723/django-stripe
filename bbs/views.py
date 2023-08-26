from django.shortcuts import render,redirect

from django.views import View
from .models import Topic

import stripe
from django.conf import settings
from django.urls import reverse_lazy

class IndexView(View):

    def get(self, request, *args, **kwargs):
        context = {}


        #ここでStripeのセッションを作る、暗号化用の公開鍵とセッションIDを引き渡し、決済処理を顧客にさせる。
        # https://dashboard.stripe.com/account から企業名を入れていないとエラーが出る点に注意
        # 自分の名前をローマ字で入れておく。

        #セッションを開始するため、秘密鍵をセットする。
        stripe.api_key = settings.STRIPE_API_KEY

        session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                
                #顧客が購入する商品(実践ではここにカートに入れた商品を格納)
                line_items=[{
                    'price_data': {
                        'currency': 'jpy',
                        'product_data': {
                            'name': 'T-shirt',
                            },
                        'unit_amount': 2000,
                        },
                    'quantity': 1,
                    }],
                
                mode='payment',

                #決済成功した後のリダイレクト先
                success_url=request.build_absolute_uri(reverse_lazy("bbs:checkout")) + "?session_id={CHECKOUT_SESSION_ID}",

                #決済キャンセルしたときのリダイレクト先
                cancel_url=request.build_absolute_uri(reverse_lazy("bbs:index")),
                )

        print(session)

        #この公開鍵を使ってテンプレート上のJavaScriptにセットする。顧客が入力する情報を暗号化させるための物
        context["public_key"]   = settings.STRIPE_PUBLISHABLE_KEY

        #このStripeのセッションIDをテンプレート上のJavaScriptにセットする。上記のビューで作ったセッションを顧客に渡して決済させるための物
        context["session_id"]   = session["id"]



        return render(request,"bbs/index.html",context)

    def post(self, request, *args, **kwargs):

        posted  = Topic( comment = request.POST["comment"] )
        posted.save()

        return redirect("bbs:index")

index   = IndexView.as_view()





class CheckoutView(View):

    def get(self, request, *args, **kwargs):

        stripe.api_key = settings.STRIPE_API_KEY

        #セッションIDがパラメータに存在するかチェック。なければエラー画面へ
        if "session_id" not in request.GET:
            return redirect("bbs:index")

        #ここでセッションの存在チェック(存在しないセッションIDを適当に入力した場合、ここでエラーが出る。)
        try:
            session     = stripe.checkout.Session.retrieve(request.GET["session_id"])
            print(session)
        except:
            return redirect("bbs:index")


        #ここで決済完了かどうかチェックできる。(何らかの方法でセッションIDを取得し、URLに直入力した場合、ここでエラーが出る。)
        try:
            customer    = stripe.Customer.retrieve(session.customer)
            print(customer)
        except:
            return redirect("bbs:index")


        #この時点で、セッションが存在しており、なおかつ決済している状態であることがわかる。
        #TODO:実践ではここで『カート内の商品を削除する』『顧客へ注文承りましたという趣旨のメールを送信する』『注文が入った旨を関係者にメールで報告する』等の処理を書く。
        print("決済完了")


        #TODO:できればこのページは注文完了のレンダリングを
        return redirect("bbs:index")

checkout    = CheckoutView.as_view()
