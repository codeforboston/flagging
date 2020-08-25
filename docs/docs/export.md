# Export Data

## HTML iFrame

The outputs of the model can be exported as an iFrame, which allows the website's live data to be viewed on a statically rendered web page (such as those hosted by Weebly). To export the data using an iFrame, use the following HTML:

    <div style="position: relative;overflow: hidden;width: 100%;padding-top: 75%">
    <iframe src="http://crwa-flagging.herokuapp.com/flags" style="position: absolute;top: 0;left: 0;bottom: 0;right: 0; width: 100%; height: 100%"></iframe>
