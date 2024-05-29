
If you can run some code like this - only a sample here and not fully cooked - you can enable some potential self serve / all in one DNS lookup.

The problem can be solved in many ways.  This one used Internal DNS to provide a resolution.

You can add a concurrent external DNS resolution later.  Gwtting both answers in one shot can confuse people however when they bring this page's reslts to you, it let's you trust the results instead of doing this homework twice or guessing thier spelling mistake :)

NSLOOKP and DIG can do these commands.. why the page?  Aren't you lucky to have sucn a open firewall policy :)  This is not for you.

You could add a lot more to this simple example.  One thought is to also pull from the API of your internal DNS and external DNS.  Doing that may help uncover cache issues or other answers like GEO located results the app can't deduce otherwise.

Enjoy the basic internal DNS checker.