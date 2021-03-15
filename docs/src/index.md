![](img/og_preview.png)

This documentation provides developers and maintainers information about the CRWA's flagging website, including information on: deploying the website, developing the website, using the website's code locally, and using the website's admin panel.

## For Website Administrators

Read the [admin guide](../admin).

## Connecting the Widget

The outputs of the model can be exported as an iFrame, which allows the flagging website's live data to be viewed on a statically rendered web page (such as those hosted by Weebly).

To export the model outputs using an iFrame, use the following HTML:

```html
<div class="wsite-multicol"><div style="position:relative; overflow:hidden; width:100%; padding-top:75%; margin:0px; border:0px;">
<iframe onload="resizeIframe(this)" src="https://crwa-flagging-staging.herokuapp.com/flags" style="position:absolute; top:0; left:0; bottom:0; right:0; width:100%; height:100%; background-image:url('data:image/svg+xml;charset=UTF-8,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22utf-8%22%3F%3E%0A%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20xmlns%3Axlink%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxlink%22%20style%3D%22margin%3A%20auto%3B%20background%3A%20rgb(255%2C%20255%2C%20255)%20none%20repeat%20scroll%200%25%200%25%3B%20display%3A%20block%3B%20shape-rendering%3A%20auto%3B%22%20width%3D%22200px%22%20height%3D%22200px%22%20viewBox%3D%220%200%20100%20100%22%20preserveAspectRatio%3D%22xMidYMid%22%3E%0A%3Cg%20transform%3D%22rotate(0%2050%2050)%22%3E%0A%20%20%3Crect%20x%3D%2247%22%20y%3D%2224%22%20rx%3D%223%22%20ry%3D%226%22%20width%3D%226%22%20height%3D%2212%22%20fill%3D%22%236492ac%22%3E%0A%20%20%20%20%3Canimate%20attributeName%3D%22opacity%22%20values%3D%221%3B0%22%20keyTimes%3D%220%3B1%22%20dur%3D%221s%22%20begin%3D%22-0.9166666666666666s%22%20repeatCount%3D%22indefinite%22%3E%3C%2Fanimate%3E%0A%20%20%3C%2Frect%3E%0A%3C%2Fg%3E%3Cg%20transform%3D%22rotate(30%2050%2050)%22%3E%0A%20%20%3Crect%20x%3D%2247%22%20y%3D%2224%22%20rx%3D%223%22%20ry%3D%226%22%20width%3D%226%22%20height%3D%2212%22%20fill%3D%22%236492ac%22%3E%0A%20%20%20%20%3Canimate%20attributeName%3D%22opacity%22%20values%3D%221%3B0%22%20keyTimes%3D%220%3B1%22%20dur%3D%221s%22%20begin%3D%22-0.8333333333333334s%22%20repeatCount%3D%22indefinite%22%3E%3C%2Fanimate%3E%0A%20%20%3C%2Frect%3E%0A%3C%2Fg%3E%3Cg%20transform%3D%22rotate(60%2050%2050)%22%3E%0A%20%20%3Crect%20x%3D%2247%22%20y%3D%2224%22%20rx%3D%223%22%20ry%3D%226%22%20width%3D%226%22%20height%3D%2212%22%20fill%3D%22%236492ac%22%3E%0A%20%20%20%20%3Canimate%20attributeName%3D%22opacity%22%20values%3D%221%3B0%22%20keyTimes%3D%220%3B1%22%20dur%3D%221s%22%20begin%3D%22-0.75s%22%20repeatCount%3D%22indefinite%22%3E%3C%2Fanimate%3E%0A%20%20%3C%2Frect%3E%0A%3C%2Fg%3E%3Cg%20transform%3D%22rotate(90%2050%2050)%22%3E%0A%20%20%3Crect%20x%3D%2247%22%20y%3D%2224%22%20rx%3D%223%22%20ry%3D%226%22%20width%3D%226%22%20height%3D%2212%22%20fill%3D%22%236492ac%22%3E%0A%20%20%20%20%3Canimate%20attributeName%3D%22opacity%22%20values%3D%221%3B0%22%20keyTimes%3D%220%3B1%22%20dur%3D%221s%22%20begin%3D%22-0.6666666666666666s%22%20repeatCount%3D%22indefinite%22%3E%3C%2Fanimate%3E%0A%20%20%3C%2Frect%3E%0A%3C%2Fg%3E%3Cg%20transform%3D%22rotate(120%2050%2050)%22%3E%0A%20%20%3Crect%20x%3D%2247%22%20y%3D%2224%22%20rx%3D%223%22%20ry%3D%226%22%20width%3D%226%22%20height%3D%2212%22%20fill%3D%22%236492ac%22%3E%0A%20%20%20%20%3Canimate%20attributeName%3D%22opacity%22%20values%3D%221%3B0%22%20keyTimes%3D%220%3B1%22%20dur%3D%221s%22%20begin%3D%22-0.5833333333333334s%22%20repeatCount%3D%22indefinite%22%3E%3C%2Fanimate%3E%0A%20%20%3C%2Frect%3E%0A%3C%2Fg%3E%3Cg%20transform%3D%22rotate(150%2050%2050)%22%3E%0A%20%20%3Crect%20x%3D%2247%22%20y%3D%2224%22%20rx%3D%223%22%20ry%3D%226%22%20width%3D%226%22%20height%3D%2212%22%20fill%3D%22%236492ac%22%3E%0A%20%20%20%20%3Canimate%20attributeName%3D%22opacity%22%20values%3D%221%3B0%22%20keyTimes%3D%220%3B1%22%20dur%3D%221s%22%20begin%3D%22-0.5s%22%20repeatCount%3D%22indefinite%22%3E%3C%2Fanimate%3E%0A%20%20%3C%2Frect%3E%0A%3C%2Fg%3E%3Cg%20transform%3D%22rotate(180%2050%2050)%22%3E%0A%20%20%3Crect%20x%3D%2247%22%20y%3D%2224%22%20rx%3D%223%22%20ry%3D%226%22%20width%3D%226%22%20height%3D%2212%22%20fill%3D%22%236492ac%22%3E%0A%20%20%20%20%3Canimate%20attributeName%3D%22opacity%22%20values%3D%221%3B0%22%20keyTimes%3D%220%3B1%22%20dur%3D%221s%22%20begin%3D%22-0.4166666666666667s%22%20repeatCount%3D%22indefinite%22%3E%3C%2Fanimate%3E%0A%20%20%3C%2Frect%3E%0A%3C%2Fg%3E%3Cg%20transform%3D%22rotate(210%2050%2050)%22%3E%0A%20%20%3Crect%20x%3D%2247%22%20y%3D%2224%22%20rx%3D%223%22%20ry%3D%226%22%20width%3D%226%22%20height%3D%2212%22%20fill%3D%22%236492ac%22%3E%0A%20%20%20%20%3Canimate%20attributeName%3D%22opacity%22%20values%3D%221%3B0%22%20keyTimes%3D%220%3B1%22%20dur%3D%221s%22%20begin%3D%22-0.3333333333333333s%22%20repeatCount%3D%22indefinite%22%3E%3C%2Fanimate%3E%0A%20%20%3C%2Frect%3E%0A%3C%2Fg%3E%3Cg%20transform%3D%22rotate(240%2050%2050)%22%3E%0A%20%20%3Crect%20x%3D%2247%22%20y%3D%2224%22%20rx%3D%223%22%20ry%3D%226%22%20width%3D%226%22%20height%3D%2212%22%20fill%3D%22%236492ac%22%3E%0A%20%20%20%20%3Canimate%20attributeName%3D%22opacity%22%20values%3D%221%3B0%22%20keyTimes%3D%220%3B1%22%20dur%3D%221s%22%20begin%3D%22-0.25s%22%20repeatCount%3D%22indefinite%22%3E%3C%2Fanimate%3E%0A%20%20%3C%2Frect%3E%0A%3C%2Fg%3E%3Cg%20transform%3D%22rotate(270%2050%2050)%22%3E%0A%20%20%3Crect%20x%3D%2247%22%20y%3D%2224%22%20rx%3D%223%22%20ry%3D%226%22%20width%3D%226%22%20height%3D%2212%22%20fill%3D%22%236492ac%22%3E%0A%20%20%20%20%3Canimate%20attributeName%3D%22opacity%22%20values%3D%221%3B0%22%20keyTimes%3D%220%3B1%22%20dur%3D%221s%22%20begin%3D%22-0.16666666666666666s%22%20repeatCount%3D%22indefinite%22%3E%3C%2Fanimate%3E%0A%20%20%3C%2Frect%3E%0A%3C%2Fg%3E%3Cg%20transform%3D%22rotate(300%2050%2050)%22%3E%0A%20%20%3Crect%20x%3D%2247%22%20y%3D%2224%22%20rx%3D%223%22%20ry%3D%226%22%20width%3D%226%22%20height%3D%2212%22%20fill%3D%22%236492ac%22%3E%0A%20%20%20%20%3Canimate%20attributeName%3D%22opacity%22%20values%3D%221%3B0%22%20keyTimes%3D%220%3B1%22%20dur%3D%221s%22%20begin%3D%22-0.08333333333333333s%22%20repeatCount%3D%22indefinite%22%3E%3C%2Fanimate%3E%0A%20%20%3C%2Frect%3E%0A%3C%2Fg%3E%3Cg%20transform%3D%22rotate(330%2050%2050)%22%3E%0A%20%20%3Crect%20x%3D%2247%22%20y%3D%2224%22%20rx%3D%223%22%20ry%3D%226%22%20width%3D%226%22%20height%3D%2212%22%20fill%3D%22%236492ac%22%3E%0A%20%20%20%20%3Canimate%20attributeName%3D%22opacity%22%20values%3D%221%3B0%22%20keyTimes%3D%220%3B1%22%20dur%3D%221s%22%20begin%3D%220s%22%20repeatCount%3D%22indefinite%22%3E%3C%2Fanimate%3E%0A%20%20%3C%2Frect%3E%0A%3C%2Fg%3E%0A%3C!--%20%5Bldio%5D%20generated%20by%20https%3A%2F%2Floading.io%2F%20--%3E%3C%2Fsvg%3E');  background-repeat: no-repeat; background-position: center;" frameborder="0"></iframe>
</div>
<script type="text/javascript">
function resizeIframe(iframe) {
  iframe.height = iframe.contentWindow.document.body.scrollHeight + "px";
}
</script>
</div>
```

## For Developers

To locally deploy the website and start coding, follow the [setup guide](../setup).

Once you have the website setup locally, you now have access to the following:

- Deploy the website to Heroku (guide [here](../deployment))
- Manually run commands and download data through the `flask shell`.
- Make changes to the predictive model, including revising its coefficients. (Guide is currently WIP)
- (Advanced) Make other changes to the website.

## To Deploy

The website can be one-click deployed to Heroku [from the repo]({{ config.repo_url }}).

There will still be some additional configuration you should do after one-click deployment. Click [here](../cloud) for more.
