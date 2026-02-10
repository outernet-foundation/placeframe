
Photon .Net Client SDK - Readme
www.photonengine.com  -  Join our Discord Server: https://dashboard.photonengine.com/account/profile



Documentation
----------------------------------------------------------------------------------------------------
    The API reference is included in this package as CHM file.
    Find the manuals, tutorials, API reference and more online.

    https://doc.photonengine.com



Running the Demos
----------------------------------------------------------------------------------------------------
    Our demos are built for the Photon Cloud for convenience.
    The service is free for development. Signing up is instant and without obligation.

    Each application type has it's own AppId (e.g Realtime and Chat). 
    Create and manage apps via the Photon Dashboard:
    https://dashboard.photonengine.com

    From the dashboard, copy an AppId and update the property "AppId" in the source of the demos.



Chat Documentation
----------------------------------------------------------------------------------------------------
    http://doc.photonengine.com/en/chat



Implementing Photon Chat
----------------------------------------------------------------------------------------------------
    Photon Chat is separated from other Photon Applications, so it needs it's own AppId.
    Our demos usually don't have an AppId set.
    In code, find "<your appid>" to copy yours in. In Unity, we usually use a component
    to set the AppId via the Inspector. Look for the "Scripts" GameObject in the scenes.

    Register your Chat Application in the Dashboard:
    https://dashboard.photonengine.com

    The class ChatClient and the interface IChatClientListener wrap up most important parts
    of the Chat API. Please refer to their documentation on how to use this API.
    More documentation will follow.

    If you use Unity, copy the source from the ChatApi folder into your project.



Unity Notes
----------------------------------------------------------------------------------------------------
    If you don't use Unity, skip this chapter.


    We assume you are using Unity 2019.4 or newer.
    The demos are prepared to export for Standalone. Other platforms may need work on input and UI.

    The SDK contains an "Assets" folder. To import Photon into your project, copy the content
    into your project's Asset folder. You may need to setup the DLLs in the Inspector to export
    for your platform(s).


    Currently supported export platforms are:
        Standalone (Windows, OSx and Linux)
        WebGL
        iOS
        Android
        Windows UWP
        Consoles			(see: https://doc.photonengine.com/en-us/pun/current/consoles)
        XR devices          (Quest, Vision Pro / Vision OS, Hololens, Magic Leap)


    How to add Photon to your Unity project:
    1) The Unity SDK contains an "Assets" folder.
       Copy the content into your project's Assets folder.
    2) Make sure to have the following line of code in your scripts to make it run in background:
       Application.runInBackground = true; //without this Photon will loose connection if not focussed
    3) If you host a Photon Server change the server address in the client. "localhost:5055" won't work on device.
    4) Implement OnApplicationQuit() and disconnect the client when the app stops.
