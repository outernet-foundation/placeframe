// ----------------------------------------------------------------------------------------------------------------------
// <summary>The Photon Chat Api enables clients to connect to a chat server and communicate with other clients.</summary>
// <remarks>ChatClient is the main class of this api.</remarks>
// <copyright company="Exit Games GmbH">Photon Chat Api - Copyright (C) 2014 Exit Games GmbH</copyright>
// ----------------------------------------------------------------------------------------------------------------------


#if UNITY_2017_4_OR_NEWER
#define SUPPORTED_UNITY
#endif


namespace Photon.Chat
{
    using System;
    using System.Threading;
    using System.Collections.Generic;
    using Photon.Client;

    #if SUPPORTED_UNITY
    using SupportClass = Photon.Client.SupportClass;
    #endif


    /// <summary>Central class of the Photon Chat API to connect, handle channels and messages.</summary>
    /// <remarks>
    /// This class must be instantiated with a IChatClientListener instance to get the callbacks.
    /// Integrate it into your game loop by calling Service regularly. If the target platform supports Threads/Tasks,
    /// set UseBackgroundWorkerForSending = true, to let the ChatClient keep the connection by sending from
    /// an independent thread.
    ///
    /// Call Connect with an AppId that is set up as Photon Chat application. Note: Connect covers multiple
    /// messages between this client and the servers. A short workflow will connect you to a chat server.
    ///
    /// Each ChatClient resembles a user in chat (set in Connect). Each user automatically subscribes a channel
    /// for incoming private messages and can message any other user privately.
    /// Before you publish messages in any non-private channel, that channel must be subscribed.
    ///
    /// PublicChannels is a list of subscribed channels, containing messages and senders.
    /// PrivateChannels contains all incoming and sent private messages.
    /// </remarks>
    public class ChatClient : IPhotonPeerListener
    {
        /// <summary>Stores this client's ChatAppSettings, as applied by ConnectUsingSettings().</summary>
        /// <remarks>This is a unique copy of the settings passed to ConnectUsingSettings().</remarks>
        public ChatAppSettings AppSettings { get; private set; }

        const int FriendRequestListMax = 1024;

        /// <summary> Default maximum value possible for <see cref="ChatChannel.MaxSubscribers"/> when <see cref="ChatChannel.PublishSubscribers"/> is enabled</summary>
        public const int DefaultMaxSubscribers = 100;

        private const byte HttpForwardWebFlag = 0x01;

        /// <summary>Enables a fallback to another protocol in case connect to the Name Server failed.</summary>
        /// <remarks>
        /// When connecting to the Name Server fails for a first time, the client will select an alternative
        /// network protocol and re-try to connect.
        ///
        /// The fallback will use the default Name Server port as defined by ProtocolToNameServerPort.
        ///
        /// The fallback for TCP is UDP. All other protocols fallback to TCP.
        /// </remarks>
        [Obsolete("Replaced by this.AppSettings. Calling ConnectUsingSettings() will set/replace this.AppSettings.")]
        public bool EnableProtocolFallback {
            get { return this.AppSettings?.EnableProtocolFallback ?? false; }
            set
            {
                if (this.AppSettings != null) this.AppSettings.EnableProtocolFallback = value;
            }
        }

        /// <summary>Region to connect to. Photon Chat does not offer the same range of regions as other Photon products.</summary>
        private readonly string chatRegion = "eu";

        /// <summary>Settable only before you connect! Defaults to "EU".</summary>
        [Obsolete("Replaced by this.FixedRegionOrDefault. Setting a region should be done via ConnectUsingSettings() parameter AppSettings.")]
        public string ChatRegion
        {
            get
            {
                return this.FixedRegionOrDefault;
            }
        }

        /// <summary>Returns the AppSettings.FixedRegion (if set) or the default region: "EU".</summary>
        public string FixedRegionOrDefault
        {
            get
            {
                if (this.AppSettings != null && !string.IsNullOrEmpty(this.AppSettings.FixedRegion))
                {
                    return this.AppSettings.FixedRegion;
                }

                return this.chatRegion;
            }
        }

        /// <summary>
        /// Defines a proxy URL for WebSocket connections. Can be the proxy or point to a .pac file.
        /// </summary>
        /// <remarks>
        /// This URL supports various definitions:
        ///
        /// "user:pass@proxyaddress:port"<br/>
        /// "proxyaddress:port"<br/>
        /// "system:"<br/>
        /// "pac:"<br/>
        /// "pac:http://host/path/pacfile.pac"<br/>
        ///
        /// Important: Don't define a protocol, except to point to a pac file. the proxy address should not begin with http:// or https://.
        /// </remarks>
        [Obsolete("Replaced by this.AppSettings. Calling ConnectUsingSettings() will set/replace this.AppSettings.")]
        public string ProxyServerAddress
        {
            get { return this.AppSettings?.ProxyServer ?? null; }
        }


        /// <summary>The currently used server address (if any). The type of server is identified by the State.</summary>
        public string CurrentServerAddress { get { return this.Peer.ServerAddress; } }

        /// <summary>The address of the actual chat server assigned from NameServer. Null until connected to a frontend.</summary>
        public string FrontendAddress { get; private set; }


        /// <summary>Current state of the ChatClient. Also use CanChat.</summary>
        public ChatState State { get; private set; }

        /// <summary> Disconnection cause. Check this inside <see cref="IChatClientListener.OnDisconnected"/>. </summary>
        public ChatDisconnectCause DisconnectedCause { get; private set; }

        /// <summary>
        /// Sets the level (and amount) of debug output provided by the PhotonPeer (even while connected).
        /// </summary>
        /// <remarks>
        /// Sets this.Peer.LogLevel for immediate effect and also updates this.AppSettings.NetworkLogging.
        /// This affects the callbacks to IChatClientListener.DebugReturn.
        /// Default Level: Error.
        /// </remarks>
        public LogLevel LogLevelPeer
        {
            set
            {
                this.Peer.LogLevel = value;
                this.AppSettings.NetworkLogging = value;
            }
            get { return this.Peer.LogLevel; }
        }
        
        /// <summary>
        /// Sets the level (and amount) of debug output provided by the ChatClient. Accessor for AppSettings.ClientLogging.
        /// </summary>
        /// <remarks>
        /// This affects the callbacks to IChatClientListener.DebugReturn.
        /// Default Level: Warning.
        /// </remarks>
        public LogLevel LogLevelClient
        {
            set { this.AppSettings.ClientLogging = value; }
            get { return this.AppSettings.ClientLogging; }
        }

        /// <summary>
        /// Checks if this client is ready to send messages.
        /// </summary>
        public bool CanChat
        {
            get { return this.State == ChatState.ConnectedToFrontEnd; }
        }

        /// <summary>
        /// Checks if this client is ready to publish messages inside a public channel.
        /// </summary>
        /// <param name="channelName">The channel to do the check with.</param>
        /// <returns>Whether or not this client is ready to publish messages inside the public channel with the specified channelName.</returns>
        public bool CanChatInChannel(string channelName)
        {
            return this.CanChat && this.PublicChannels.ContainsKey(channelName) && !this.PublicChannelsUnsubscribing.Contains(channelName);
        }

        /// <summary>The version of your client. A new version also creates a new "virtual app" to separate players from older client versions.</summary>
        [Obsolete("Replaced by this.AppSettings. Calling ConnectUsingSettings() will set/replace this.AppSettings.")]
        public string AppVersion
        {
            get { return this.AppSettings?.AppVersion ?? null; }
        }

        /// <summary>The AppID as assigned from the Photon Cloud.</summary>
        [Obsolete("Replaced by this.AppSettings. Calling ConnectUsingSettings() will set/replace this.AppSettings.")]
        public string AppId
        {
            get { return this.AppSettings?.AppIdChat ?? null; }
        }


        /// <summary>Settable only before you connect!</summary>
        public AuthenticationValues AuthValues { get; set; }

        /// <summary>The unique ID of a user/person, stored in AuthValues.UserId. Set it before you connect.</summary>
        /// <remarks>
        /// This value wraps AuthValues.UserId.
        /// It's not a nickname and we assume users with the same userID are the same person.</remarks>
        public string UserId
        {
            get
            {
                return (this.AuthValues != null) ? this.AuthValues.UserId : null;
            }
            private set
            {
                if (this.AuthValues == null)
                {
                    this.AuthValues = new AuthenticationValues();
                }
                this.AuthValues.UserId = value;
            }
        }

        /// <summary>If greater than 0, new channels will limit the number of messages they cache locally.</summary>
        /// <remarks>
        /// This can be useful to limit the amount of memory used by chats.
        /// You can set a MessageLimit per channel but this value gets applied to new ones.
        ///
        /// Note:
        /// Changing this value, does not affect ChatChannels that are already in use!
        /// </remarks>
        public int MessageLimit;

        /// <summary>Limits the number of messages from private channel histories.</summary>
        /// <remarks>
        /// This is applied to all private channels on reconnect, as there is no explicit re-joining private channels.<br/>
        /// Default is -1, which gets available messages up to a maximum set by the server.<br/>
        /// A value of 0 gets you zero messages.<br/>
        /// The server's limit of messages may be lower. If so, the server's value will overrule this.<br/>
        /// </remarks>
        public int PrivateChatHistoryLength = -1;

        /// <summary> Public channels this client is subscribed to. </summary>
        public readonly Dictionary<string, ChatChannel> PublicChannels;
        /// <summary> Private channels in which this client has exchanged messages. </summary>
        public readonly Dictionary<string, ChatChannel> PrivateChannels;

        // channels being in unsubscribing process
        // items will be removed on successful unsubscription or subscription (the latter required after attempt to unsubscribe from not existing channel)
        private readonly HashSet<string> PublicChannelsUnsubscribing;

        private readonly IChatClientListener listener = null;

        /// <summary> The Chat Peer used by this client.</summary>
        public readonly PhotonPeer Peer;

        private const string ChatAppName = "chat";
        private bool didAuthenticate;

        private int msDeltaForServiceCalls = 50;
        private Timer stateTimer;
        private int msTimestampOfLastServiceCall;

        /// <summary>Defines if Connect should create a Timer to send outgoing messages and keep the connection up. No effect in WebGL.</summary>
        /// <remarks>
        /// Defines if a background Timer is used to call SendOutgoingCommands, while your code calls Service to dispatch received messages.
        /// The benefit is:
        ///
        /// Even if your game logic is being paused, the Timer will keep up the connection to the server.
        /// On a lower level, acknowledgments and pings will prevent a server-side timeout while (e.g.) Unity loads assets.
        ///
        /// Your game logic still has to call Service regularly to dispatch received messages.
        /// As this typically triggers UI updates, it's easier to call Service from the main thread.
        ///
        /// On WebGL exports, the Timer feature is not available, so Connect will set UseBackgroundWorkerForSending = false and log about it.
        /// Make sure ChatClient.Service is called regularly.
        /// </remarks>
        public bool UseBackgroundWorkerForSending { get; set; }

        /// <summary>Exposes the TransportProtocol of the used PhotonPeer. Settable while not connected.</summary>
        public ConnectionProtocol TransportProtocol
        {
            get { return this.Peer.TransportProtocol; }
            private set
            {
                if (this.Peer == null || this.Peer.PeerState != PeerStateValue.Disconnected)
                {
                    this.listener.DebugReturn(LogLevel.Warning, "Can't set TransportProtocol. Disconnect first! " + ((this.Peer != null) ? "PeerState: " + this.Peer.PeerState : "The Peer is null."));
                    return;
                }
                this.Peer.TransportProtocol = value;
            }
        }

        /// <summary>Defines which PhotonSocket implementation to use per ConnectionProtocol.</summary>
        /// <remarks>
        /// Several platforms have special Socket implementations and slightly different APIs.
        /// To accomodate this, switching the socket implementation for a network protocol was made available.
        /// By default, UDP and TCP have socket implementations assigned.
        ///
        /// You only need to set the SocketImplementationConfig once, after creating a PhotonPeer
        /// and before connecting. If you switch the TransportProtocol, the correct implementation is being used.
        /// </remarks>
        public Dictionary<ConnectionProtocol, Type> SocketImplementationConfig
        {
            get { return this.Peer.SocketImplementationConfig; }
        }

        /// <summary>
        /// Chat client constructor.
        /// </summary>
        /// <param name="listener">The chat listener implementation.</param>
        /// <param name="protocol">Connection protocol to be used by this client. Default is <see cref="ConnectionProtocol.Udp"/>.</param>
        public ChatClient(IChatClientListener listener, ConnectionProtocol protocol = ConnectionProtocol.Udp)
        {
            this.listener = listener;
            this.State = ChatState.Uninitialized;

            this.AppSettings = new ChatAppSettings();

            this.Peer = new PhotonPeer(this, protocol);
            this.Peer.SerializationProtocolType = SerializationProtocol.GpBinaryV18;

            this.ConfigUnitySockets();

            this.PublicChannels = new Dictionary<string, ChatChannel>();
            this.PrivateChannels = new Dictionary<string, ChatChannel>();

            this.PublicChannelsUnsubscribing = new HashSet<string>();
        }


        /// <summary>
        /// Applies appSettings and authValues (even if null) and connects to the Photon Chat Cloud.
        /// </summary>
        /// <param name="appSettings">Used to set up the AppId, Server Address, Port, etc. before connecting. Check reference for ChatAppSettings.</param>
        /// <param name="authValues">This value will set this.AuthValues, even if null.</param>
        public bool ConnectUsingSettings(ChatAppSettings appSettings, AuthenticationValues authValues)
        {
            this.AuthValues = authValues;
            return this.ConnectUsingSettings(appSettings);
        }

        /// <summary>
        /// Applies initial appSettings and connects to the Photon Chat Cloud.
        /// </summary>
        /// <remarks>
        /// This method initializes the ChatClient with the given ChatAppSettings.
        ///
        /// The appSettings argument gets copied into chatClient.AppSettings,
        /// which is then independent of your reference.
        ///
        /// While the client is connected, changing values in the chatClient.AppSettings
        /// will not have an effect on the connection in most cases. For example, the
        /// Server, TransportProtocol and Port are immutable for an established connection.
        ///
        /// The log level for the Peer must be set via: chatClient.LogLevelPeer.
        /// </remarks>
        public bool ConnectUsingSettings(ChatAppSettings appSettings)
        {
            if (appSettings == null)
            {
                this.listener.DebugReturn(LogLevel.Error, "ConnectUsingSettings() failed. The appSettings can't be null.'");
                return false;
            }

            //using a copy of the ChatAppSettings so they are independent of the outside
            this.AppSettings = new ChatAppSettings(appSettings);


            this.LogLevelPeer = appSettings.NetworkLogging;
            this.TransportProtocol = appSettings.Protocol;


            if (!appSettings.IsDefaultNameServer)
            {
                this.NameServerHost = appSettings.Server;
            }
            this.NameServerPortOverride = appSettings.IsDefaultPort ? (ushort)0 : appSettings.Port;


            return this.ConnectIntern();
        }


        /// <summary>
        /// Obsolete. Connects this client to the Photon Chat Cloud.
        /// </summary>
        [Obsolete("Use ConnectUsingSettings, which is more feature complete.")]
        public bool Connect(string appId, string appVersion, AuthenticationValues authValues)
        {
            if (authValues != null)
            {
                this.AuthValues = authValues;
            }

            this.AppSettings.AppIdChat = appId;
            this.AppSettings.AppVersion = appVersion;

            return this.ConnectIntern();
        }


        /// <summary>Intern method to reset client and connect to chat server.</summary>
        private bool ConnectIntern()
        {
            this.Peer.PingInterval = 3000;
            this.Peer.QuickResendAttempts = 2;
            this.Peer.MaxResends = 7;

            // clean all channels
            this.PublicChannels.Clear();
            this.PrivateChannels.Clear();
            this.PublicChannelsUnsubscribing.Clear();

            this.DisconnectedCause = ChatDisconnectCause.None;
            this.didAuthenticate = false;


            #if UNITY_WEBGL
            if (this.TransportProtocol == ConnectionProtocol.Tcp || this.TransportProtocol == ConnectionProtocol.Udp)
            {
                this.listener.DebugReturn(LogLevel.Warning, "WebGL requires WebSockets. Switching TransportProtocol to WebSocketSecure.");
                this.TransportProtocol = ConnectionProtocol.WebSocketSecure;
            }
            if (this.UseBackgroundWorkerForSending)
            {
                this.UseBackgroundWorkerForSending = false;
                this.listener.DebugReturn(LogLevel.Info, "WebGL does not support using UseBackgroundWorkerForSending (due to lack of the Timer class). Service() will send messages.");
            }
            #endif


            bool isConnecting = this.Peer.Connect(this.NameServerAddress, this.AppSettings.AppIdChat, null, proxyServerAddress: this.AppSettings.ProxyServer);
            if (isConnecting)
            {
                this.State = ChatState.ConnectingToNameServer;
            }

            if (this.UseBackgroundWorkerForSending)
            {
                this.stateTimer = new Timer(this.SendOutgoingInBackground, null, this.msDeltaForServiceCalls, this.msDeltaForServiceCalls);
            }

            return isConnecting;
        }


        /// <summary>
        /// Must be called regularly to keep connection between client and server alive and to process incoming messages.
        /// </summary>
        /// <remarks>
        /// This method limits the effort it does automatically using the private variable msDeltaForServiceCalls.
        /// That value is lower for connect and multiplied by 4 when chat-server connection is ready.
        /// </remarks>
        public void Service()
        {
            // Dispatch until every already-received message got dispatched
            while (this.Peer.DispatchIncomingCommands())
            {
            }

            // if there is no background thread for sending, Service() will do that as well, in intervals
            if (!this.UseBackgroundWorkerForSending)
            {
                if (Environment.TickCount - this.msTimestampOfLastServiceCall > this.msDeltaForServiceCalls || this.msTimestampOfLastServiceCall == 0)
                {
                    this.msTimestampOfLastServiceCall = Environment.TickCount;

                    while (this.Peer.SendOutgoingCommands())
                    {
                    }
                }
            }
        }

        /// <summary>
        /// Called by a separate thread, this sends outgoing commands of this peer, as long as it's connected.
        /// </summary>
        /// <returns>True as long as the client is not disconnected.</returns>
        private void SendOutgoingInBackground(object state = null)
        {
            bool moreToSend = true;
            while (this.State != ChatState.Disconnected && moreToSend)
            {
                moreToSend = this.Peer.SendOutgoingCommands();
            }
        }

        /// <summary>
        /// Disconnects from the Chat Server by sending a "disconnect command", which prevents a timeout server-side.
        /// </summary>
        public void Disconnect(ChatDisconnectCause cause = ChatDisconnectCause.DisconnectByClientLogic)
        {
            if (this.State == ChatState.Disconnecting || this.State == ChatState.Uninitialized)
            {
                this.listener.DebugReturn(LogLevel.Info, "Disconnect() call gets skipped due to State " + this.State + ". DisconnectedCause: " + this.DisconnectedCause + " Parameter cause: " + cause);
                return;
            }

            if (this.DisconnectedCause == ChatDisconnectCause.None)
            {
                this.DisconnectedCause = cause;
            }

            if (this.Peer.PeerState != PeerStateValue.Disconnected)
            {
                this.State = ChatState.Disconnecting;
                this.Peer.Disconnect();
            }
        }

        /// <summary>
        /// Sends operation to subscribe to a list of channels by name and possibly retrieve messages we did not receive while unsubscribed.
        /// </summary>
        /// <param name="channels">List of channels to subscribe to. Avoid null or empty values.</param>
        /// <param name="lastMsgIds">ID of last message received per channel. Useful when re subscribing to receive only messages we missed.</param>
        /// <returns>If the operation could be sent at all (Example: Fails if not connected to Chat Server).</returns>
        public bool Subscribe(string[] channels, int[] lastMsgIds)
        {
            if (!this.CanChat)
            {
                if (this.LogLevelClient >= LogLevel.Error)
                {
                    this.listener.DebugReturn(LogLevel.Error, "Subscribe called while not connected to front end server.");
                }
                return false;
            }

            if (channels == null || channels.Length == 0)
            {
                if (this.LogLevelClient >= LogLevel.Warning)
                {
                    this.listener.DebugReturn(LogLevel.Warning, "Subscribe can't be called for empty or null channels-list.");
                }
                return false;
            }

            for (int i = 0; i < channels.Length; i++)
            {
                if (string.IsNullOrEmpty(channels[i]))
                {
                    if (this.LogLevelClient >= LogLevel.Error)
                    {
                        this.listener.DebugReturn(LogLevel.Error, string.Format("Subscribe can't be called with a null or empty channel name at index {0}.", i));
                    }
                    return false;
                }
            }

            if (lastMsgIds == null || lastMsgIds.Length != channels.Length)
            {
                if (this.LogLevelClient >= LogLevel.Error)
                {
                    this.listener.DebugReturn(LogLevel.Error, "Subscribe can't be called when \"lastMsgIds\" array is null or does not have the same length as \"channels\" array.");
                }
                return false;
            }

            ParameterDictionary opParameters = new ParameterDictionary()
            {
                { ChatParameterCode.Channels, channels },
                { ChatParameterCode.MsgIds,  lastMsgIds},
                { ChatParameterCode.HistoryLength, -1 } // server will decide how many messages to send to client
            };

            return this.Peer.SendOperation(ChatOperationCode.Subscribe, opParameters, SendOptions.SendReliable);
        }

        /// <summary>
        /// Sends operation to subscribe client to channels, optionally fetching a number of messages from the cache.
        /// </summary>
        /// <remarks>
        /// Subscribes channels will forward new messages to this user. Use PublishMessage to do so.
        /// The messages cache is limited but can be useful to get into ongoing conversations, if that's needed.
        /// </remarks>
        /// <param name="channels">List of channels to subscribe to. Avoid null or empty values.</param>
        /// <param name="messagesFromHistory">0: no history. 1 and higher: number of messages in history. -1: all available history.</param>
        /// <returns>If the operation could be sent at all (Example: Fails if not connected to Chat Server).</returns>
        public bool Subscribe(string[] channels, int messagesFromHistory = 0)
        {
            if (!this.CanChat)
            {
                if (this.LogLevelClient >= LogLevel.Error)
                {
                    this.listener.DebugReturn(LogLevel.Error, "Subscribe called while not connected to front end server.");
                }
                return false;
            }

            if (channels == null || channels.Length == 0)
            {
                if (this.LogLevelClient >= LogLevel.Warning)
                {
                    this.listener.DebugReturn(LogLevel.Warning, "Subscribe can't be called for empty or null channels-list.");
                }
                return false;
            }

            return this.SendChannelOperation(channels, (byte)ChatOperationCode.Subscribe, messagesFromHistory);
        }


        /// <summary>
        /// Subscribe to a single channel and optionally sets its well-know channel properties in case the channel is created.
        /// </summary>
        /// <param name="channel">name of the channel to subscribe to</param>
        /// <param name="lastMsgId">ID of the last received message from this channel when re subscribing to receive only missed messages, default is 0</param>
        /// <param name="messagesFromHistory">how many missed messages to receive from history, default is -1 (available history). 0 will get you no items. Positive values are capped by a server side limit.</param>
        /// <param name="creationOptions">options to be used in case the channel to subscribe to will be created.</param>
        /// <returns></returns>
        public bool Subscribe(string channel, int lastMsgId = 0, int messagesFromHistory = -1, ChannelCreationOptions creationOptions = null)
        {
            if (creationOptions == null)
            {
                creationOptions = ChannelCreationOptions.Default;
            }
            int maxSubscribers = creationOptions.MaxSubscribers;
            bool publishSubscribers = creationOptions.PublishSubscribers;
            if (maxSubscribers < 0)
            {
                if (this.LogLevelClient >= LogLevel.Error)
                {
                    this.listener.DebugReturn(LogLevel.Error, "Cannot set MaxSubscribers < 0.");
                }
                return false;
            }
            if (lastMsgId < 0)
            {
                if (this.LogLevelClient >= LogLevel.Error)
                {
                    this.listener.DebugReturn(LogLevel.Error, "lastMsgId cannot be < 0.");
                }
                return false;
            }
            if (messagesFromHistory < -1)
            {
                if (this.LogLevelClient >= LogLevel.Warning)
                {
                    this.listener.DebugReturn(LogLevel.Warning, "messagesFromHistory < -1, setting it to -1");
                }
                messagesFromHistory = -1;
            }
            if (lastMsgId > 0 && messagesFromHistory == 0)
            {
                if (this.LogLevelClient >= LogLevel.Warning)
                {
                    this.listener.DebugReturn(LogLevel.Warning, "lastMsgId will be ignored because messagesFromHistory == 0");
                }
                lastMsgId = 0;
            }
            Dictionary<object, object> properties = null;
            if (publishSubscribers)
            {
                if (maxSubscribers > DefaultMaxSubscribers)
                {
                    if (this.LogLevelClient >= LogLevel.Error)
                    {
                        this.listener.DebugReturn(LogLevel.Error,
                            string.Format("Cannot set MaxSubscribers > {0} when PublishSubscribers == true.", DefaultMaxSubscribers));
                    }
                    return false;
                }
                properties = new Dictionary<object, object>();
                properties[ChannelWellKnownProperties.PublishSubscribers] = true;
            }
            if (maxSubscribers > 0)
            {
                if (properties == null)
                {
                    properties = new Dictionary<object, object>();
                }
                properties[ChannelWellKnownProperties.MaxSubscribers] = maxSubscribers;
            }
            #if CHAT_EXTENDED
            if (creationOptions.CustomProperties != null && creationOptions.CustomProperties.Count > 0)
            {
                foreach (var pair in creationOptions.CustomProperties)
                {
                    properties.Add(pair.Key, pair.Value);
                }
            }
            #endif

            ParameterDictionary opParameters = new ParameterDictionary() { { ChatParameterCode.Channels, new[] { channel } } };
            if (messagesFromHistory != 0)
            {
                opParameters.Add(ChatParameterCode.HistoryLength, messagesFromHistory);
            }
            if (lastMsgId > 0)
            {
                opParameters.Add(ChatParameterCode.MsgIds, new[] { lastMsgId });
            }
            if (properties != null && properties.Count > 0)
            {
                opParameters.Add(ChatParameterCode.Properties, properties);
            }

            return this.Peer.SendOperation(ChatOperationCode.Subscribe, opParameters, SendOptions.SendReliable);
        }


        /// <summary>Unsubscribes from a list of channels, which stops getting messages from those.</summary>
        /// <remarks>
        /// The client will remove these channels from the PublicChannels dictionary once the server sent a response to this request.
        ///
        /// The request will be sent to the server and IChatClientListener.OnUnsubscribed gets called when the server
        /// actually removed the channel subscriptions.
        ///
        /// Unsubscribe will fail if you include null or empty channel names.
        /// </remarks>
        /// <param name="channels">Names of channels to unsubscribe.</param>
        /// <returns>False, if not connected to a chat server.</returns>
        public bool Unsubscribe(string[] channels)
        {
            if (!this.CanChat)
            {
                if (this.LogLevelClient >= LogLevel.Error)
                {
                    this.listener.DebugReturn(LogLevel.Error, "Unsubscribe called while not connected to front end server.");
                }
                return false;
            }

            if (channels == null || channels.Length == 0)
            {
                if (this.LogLevelClient >= LogLevel.Warning)
                {
                    this.listener.DebugReturn(LogLevel.Warning, "Unsubscribe can't be called for empty or null channels-list.");
                }
                return false;
            }

            foreach (string ch in channels)
            {
                this.PublicChannelsUnsubscribing.Add(ch);
            }
            return this.SendChannelOperation(channels, ChatOperationCode.Unsubscribe, 0);
        }


        /// <summary>Sends a message to a public channel which this client subscribed to.</summary>
        /// <remarks>
        /// Before you publish to a channel, you have to subscribe it.
        /// Everyone in that channel will get the message.
        /// </remarks>
        /// <param name="channelName">Name of the channel to publish to.</param>
        /// <param name="message">Your message (string or any serializable data).</param>
        /// <param name="forwardAsWebhook">Optionally, public messages can be forwarded as webhooks. Configure webhooks for your Chat app to use this.</param>
        /// <returns>False if the client is not yet ready to send messages.</returns>
        public bool PublishMessage(string channelName, object message, bool forwardAsWebhook = false)
        {
            return this.publishMessage(channelName, message, true, forwardAsWebhook);
        }

        internal bool PublishMessageUnreliable(string channelName, object message, bool forwardAsWebhook = false)
        {
            return this.publishMessage(channelName, message, false, forwardAsWebhook);
        }

        private bool publishMessage(string channelName, object message, bool reliable, bool forwardAsWebhook = false)
        {
            if (!this.CanChat)
            {
                if (this.LogLevelClient >= LogLevel.Error)
                {
                    this.listener.DebugReturn(LogLevel.Error, "PublishMessage called while not connected to front end server.");
                }
                return false;
            }

            if (string.IsNullOrEmpty(channelName) || message == null)
            {
                if (this.LogLevelClient >= LogLevel.Warning)
                {
                    this.listener.DebugReturn(LogLevel.Warning, "PublishMessage parameters must be non-null and not empty.");
                }
                return false;
            }

            ParameterDictionary opParameters = new ParameterDictionary()
                {
                    { (byte)ChatParameterCode.Channel, channelName },
                    { (byte)ChatParameterCode.Message, message }
                };

            if (forwardAsWebhook)
            {
                opParameters.Add(ChatParameterCode.WebFlags, (byte)0x1);
            }

            return this.Peer.SendOperation(ChatOperationCode.Publish, opParameters, new SendOptions() { Reliability = reliable });
        }

        /// <summary>
        /// Sends a private message to a single target user. Calls OnPrivateMessage on the receiving client.
        /// </summary>
        /// <param name="target">Username to send this message to.</param>
        /// <param name="message">The message you want to send. Can be a simple string or anything serializable.</param>
        /// <param name="forwardAsWebhook">Optionally, private messages can be forwarded as webhooks. Configure webhooks for your Chat app to use this.</param>
        /// <returns>True if this clients can send the message to the server.</returns>
        public bool SendPrivateMessage(string target, object message, bool forwardAsWebhook = false)
        {
            return this.SendPrivateMessage(target, message, false, forwardAsWebhook);
        }

        /// <summary>
        /// Sends a private message to a single target user. Calls OnPrivateMessage on the receiving client.
        /// </summary>
        /// <param name="target">Username to send this message to.</param>
        /// <param name="message">The message you want to send. Can be a simple string or anything serializable.</param>
        /// <param name="encrypt">Optionally, private messages can be encrypted. Encryption is not end-to-end as the server decrypts the message.</param>
        /// <param name="forwardAsWebhook">Optionally, private messages can be forwarded as webhooks. Configure webhooks for your Chat app to use this.</param>
        /// <returns>True if this clients can send the message to the server.</returns>
        public bool SendPrivateMessage(string target, object message, bool encrypt, bool forwardAsWebhook)
        {
            return this.sendPrivateMessage(target, message, encrypt, true, forwardAsWebhook);
        }

        internal bool SendPrivateMessageUnreliable(string target, object message, bool encrypt, bool forwardAsWebhook = false)
        {
            return this.sendPrivateMessage(target, message, encrypt, false, forwardAsWebhook);
        }

        private bool sendPrivateMessage(string target, object message, bool encrypt, bool reliable, bool forwardAsWebhook = false)
        {
            if (!this.CanChat)
            {
                if (this.LogLevelClient >= LogLevel.Error)
                {
                    this.listener.DebugReturn(LogLevel.Error, "SendPrivateMessage called while not connected to front end server.");
                }
                return false;
            }

            if (string.IsNullOrEmpty(target) || message == null)
            {
                if (this.LogLevelClient >= LogLevel.Warning)
                {
                    this.listener.DebugReturn(LogLevel.Warning, "SendPrivateMessage parameters must be non-null and not empty.");
                }
                return false;
            }

            ParameterDictionary opParameters = new ParameterDictionary()
                                               {
                                                   { ChatParameterCode.UserId, target },
                                                   { ChatParameterCode.Message, message }
                                               };

            if (forwardAsWebhook)
            {
                opParameters.Add(ChatParameterCode.WebFlags, (byte)0x1);
            }

            return this.Peer.SendOperation(ChatOperationCode.SendPrivate, opParameters, new SendOptions() { Reliability = reliable, Encrypt = encrypt });
        }


        /// <summary>Sets the user's status (pre-defined or custom) and an optional message.</summary>
        /// <remarks>
        /// The predefined status values can be found in class ChatUserStatus.
        /// State ChatUserStatus.Invisible will make you offline for everyone and send no message.
        ///
        /// You can set custom values in the status integer. Aside from the pre-configured ones,
        /// all states will be considered visible and online. Else, no one would see the custom state.
        ///
        /// The message object can be anything that Photon can serialize, including (but not limited to)
        /// PhotonHashtable, object[] and string. This value is defined by your own conventions.
        /// </remarks>
        /// <param name="status">Predefined states are in class ChatUserStatus. Other values can be used at will.</param>
        /// <param name="message">Optional string message or null.</param>
        /// <param name="skipMessage">If true, the message gets ignored. It can be null but won't replace any current message.</param>
        /// <returns>True if the operation gets called on the server.</returns>
        public bool SetOnlineStatus(int status, object message = null, bool skipMessage = false)
        {
            if (!this.CanChat)
            {
                if (this.LogLevelClient >= LogLevel.Error)
                {
                    this.listener.DebugReturn(LogLevel.Error, "SetOnlineStatus called while not connected to front end server.");
                }
                return false;
            }

            ParameterDictionary opParameters = new ParameterDictionary()
                                               {
                                                   { ChatParameterCode.Status, status },
                                               };

            if (skipMessage)
            {
                opParameters[ChatParameterCode.SkipMessage] = true;
            }
            else
            {
                opParameters[ChatParameterCode.Message] = message;
            }

            return this.Peer.SendOperation(ChatOperationCode.UpdateStatus, opParameters, SendOptions.SendReliable);
        }


        /// <summary>
        /// Adds friends to a list on the Chat Server which will send you status updates for those.
        /// </summary>
        /// <remarks>
        /// AddFriends and RemoveFriends enable clients to handle their friend list
        /// in the Photon Chat server. Having users on your friends list gives you access
        /// to their current online status (and whatever info your client sets in it).
        ///
        /// Each user can set an online status consisting of an integer and an arbitrary
        /// (serializable) object. The object can be null, PhotonHashtable, object[] or anything
        /// else Photon can serialize.
        ///
        /// The status is published automatically to friends (anyone who set your user ID
        /// with AddFriends).
        ///
        /// Photon flushes friends-list when a chat client disconnects, so it has to be
        /// set each time. If your community API gives you access to online status already,
        /// you could filter and set online friends in AddFriends.
        ///
        /// Actual friend relations are not persistent and have to be stored outside
        /// of Photon.
        /// </remarks>
        /// <param name="friends">Array of friend userIds.</param>
        /// <returns>If the operation could be sent.</returns>
        public bool AddFriends(string[] friends)
        {
            if (!this.CanChat)
            {
                if (this.LogLevelClient >= LogLevel.Error)
                {
                    this.listener.DebugReturn(LogLevel.Error, "AddFriends called while not connected to front end server.");
                }
                return false;
            }

            if (friends == null || friends.Length == 0)
            {
                if (this.LogLevelClient >= LogLevel.Warning)
                {
                    this.listener.DebugReturn(LogLevel.Warning, "AddFriends can't be called for empty or null list.");
                }
                return false;
            }
            if (friends.Length > FriendRequestListMax)
            {
                if (this.LogLevelClient >= LogLevel.Warning)
                {
                    this.listener.DebugReturn(LogLevel.Warning, "AddFriends max list size exceeded: " + friends.Length + " > " + FriendRequestListMax);
                }
                return false;
            }

            ParameterDictionary opParameters = new ParameterDictionary()
                                               {
                                                   { ChatParameterCode.Friends, friends },
                                               };

            return this.Peer.SendOperation(ChatOperationCode.AddFriends, opParameters, SendOptions.SendReliable);
        }

        /// <summary>
        /// Removes the provided entries from the list on the Chat Server and stops their status updates.
        /// </summary>
        /// <remarks>
        /// Photon flushes friends-list when a chat client disconnects. Unless you want to
        /// remove individual entries, you don't have to RemoveFriends.
        ///
        /// AddFriends and RemoveFriends enable clients to handle their friend list
        /// in the Photon Chat server. Having users on your friends list gives you access
        /// to their current online status (and whatever info your client sets in it).
        ///
        /// Each user can set an online status consisting of an integer and an arbitratry
        /// (serializable) object. The object can be null, PhotonHashtable, object[] or anything
        /// else Photon can serialize.
        ///
        /// The status is published automatically to friends (anyone who set your user ID
        /// with AddFriends).
        ///
        /// Photon flushes friends-list when a chat client disconnects, so it has to be
        /// set each time. If your community API gives you access to online status already,
        /// you could filter and set online friends in AddFriends.
        ///
        /// Actual friend relations are not persistent and have to be stored outside
        /// of Photon.
        ///
        /// AddFriends and RemoveFriends enable clients to handle their friend list
        /// in the Photon Chat server. Having users on your friends list gives you access
        /// to their current online status (and whatever info your client sets in it).
        ///
        /// Each user can set an online status consisting of an integer and an arbitratry
        /// (serializable) object. The object can be null, PhotonHashtable, object[] or anything
        /// else Photon can serialize.
        ///
        /// The status is published automatically to friends (anyone who set your user ID
        /// with AddFriends).
        ///
        ///
        /// Actual friend relations are not persistent and have to be stored outside
        /// of Photon.
        /// </remarks>
        /// <param name="friends">Array of friend userIds.</param>
        /// <returns>If the operation could be sent.</returns>
        public bool RemoveFriends(string[] friends)
        {
            if (!this.CanChat)
            {
                if (this.LogLevelClient >= LogLevel.Error)
                {
                    this.listener.DebugReturn(LogLevel.Error, "RemoveFriends called while not connected to front end server.");
                }
                return false;
            }

            if (friends == null || friends.Length == 0)
            {
                if (this.LogLevelClient >= LogLevel.Warning)
                {
                    this.listener.DebugReturn(LogLevel.Warning, "RemoveFriends can't be called for empty or null list.");
                }
                return false;
            }
            if (friends.Length > FriendRequestListMax)
            {
                if (this.LogLevelClient >= LogLevel.Warning)
                {
                    this.listener.DebugReturn(LogLevel.Warning, "RemoveFriends max list size exceeded: " + friends.Length + " > " + FriendRequestListMax);
                }
                return false;
            }

            ParameterDictionary opParameters = new ParameterDictionary()
                                               {
                                                   { ChatParameterCode.Friends, friends },
                                               };

            return this.Peer.SendOperation(ChatOperationCode.RemoveFriends, opParameters, SendOptions.SendReliable);
        }


        /// <summary>
        /// Get you the (locally used) channel name for the chat between this client and another user.
        /// </summary>
        /// <param name="userName">Remote user's name or UserId.</param>
        /// <returns>The (locally used) channel name for a private channel.</returns>
        /// <remarks>Do not subscribe to this channel.
        /// Private channels do not need to be explicitly subscribed to.
        /// Use this for debugging purposes mainly.</remarks>
        public string GetPrivateChannelNameByUser(string userName)
        {
            return string.Format("{0}:{1}", this.UserId, userName);
        }

        /// <summary>
        /// Simplified access to either private or public channels by name.
        /// </summary>
        /// <param name="channelName">Name of the channel to get. For private channels, the channel-name is composed of both user's names.</param>
        /// <param name="isPrivate">Define if you expect a private or public channel.</param>
        /// <param name="channel">Out parameter gives you the found channel, if any.</param>
        /// <returns>True if the channel was found.</returns>
        /// <remarks>Public channels exist only when subscribed to them.
        /// Private channels exist only when at least one message is exchanged with the target user privately.</remarks>
        public bool TryGetChannel(string channelName, bool isPrivate, out ChatChannel channel)
        {
            if (!isPrivate)
            {
                return this.PublicChannels.TryGetValue(channelName, out channel);
            }
            else
            {
                return this.PrivateChannels.TryGetValue(channelName, out channel);
            }
        }

        /// <summary>
        /// Simplified access to all channels by name. Checks public channels first, then private ones.
        /// </summary>
        /// <param name="channelName">Name of the channel to get.</param>
        /// <param name="channel">Out parameter gives you the found channel, if any.</param>
        /// <returns>True if the channel was found.</returns>
        /// <remarks>Public channels exist only when subscribed to them.
        /// Private channels exist only when at least one message is exchanged with the target user privately.</remarks>
        public bool TryGetChannel(string channelName, out ChatChannel channel)
        {
            bool found = false;
            found = this.PublicChannels.TryGetValue(channelName, out channel);
            if (found) return true;

            found = this.PrivateChannels.TryGetValue(channelName, out channel);
            return found;
        }

        /// <summary>
        /// Simplified access to private channels by target user.
        /// </summary>
        /// <param name="userId">UserId of the target user in the private channel.</param>
        /// <param name="channel">Out parameter gives you the found channel, if any.</param>
        /// <returns>True if the channel was found.</returns>
        public bool TryGetPrivateChannelByUser(string userId, out ChatChannel channel)
        {
            channel = null;
            if (string.IsNullOrEmpty(userId))
            {
                return false;
            }
            string channelName = this.GetPrivateChannelNameByUser(userId);
            return this.TryGetChannel(channelName, true, out channel);
        }


        #region Private methods area

        #region IPhotonPeerListener implementation

        void IPhotonPeerListener.DebugReturn(LogLevel level, string message)
        {
            this.listener.DebugReturn(level, message);
        }

        void IPhotonPeerListener.OnEvent(EventData eventData)
        {
            switch (eventData.Code)
            {
                case ChatEventCode.ChatMessages:
                    this.HandleChatMessagesEvent(eventData);
                    break;
                case ChatEventCode.PrivateMessage:
                    this.HandlePrivateMessageEvent(eventData);
                    break;
                case ChatEventCode.StatusUpdate:
                    this.HandleStatusUpdate(eventData);
                    break;
                case ChatEventCode.Subscribe:
                    this.HandleSubscribeEvent(eventData);
                    break;
                case ChatEventCode.Unsubscribe:
                    this.HandleUnsubscribeEvent(eventData);
                    break;
                case ChatEventCode.UserSubscribed:
                    this.HandleUserSubscribedEvent(eventData);
                    break;
                case ChatEventCode.UserUnsubscribed:
                    this.HandleUserUnsubscribedEvent(eventData);
                    break;
                #if CHAT_EXTENDED
                case ChatEventCode.PropertiesChanged:
                    this.HandlePropertiesChanged(eventData);
                    break;
                case ChatEventCode.ErrorInfo:
                    this.HandleErrorInfoEvent(eventData);
                    break;
                #endif
            }
        }

        void IPhotonPeerListener.OnOperationResponse(OperationResponse operationResponse)
        {
            // if the operation limit was reached, disconnect (but still execute the operation response).
            if (operationResponse.ReturnCode == ErrorCode.OperationLimitReached)
            {
                this.Disconnect(ChatDisconnectCause.DisconnectByOperationLimit);
            }

            switch (operationResponse.OperationCode)
            {
                case (byte)ChatOperationCode.Authenticate:
                case (byte)ChatOperationCode.AuthenticateOnce:
                    this.HandleAuthResponse(operationResponse);
                    break;

                // the following operations usually don't return useful data and no error.
                case (byte)ChatOperationCode.Subscribe:
                case (byte)ChatOperationCode.Unsubscribe:
                case (byte)ChatOperationCode.Publish:
                case (byte)ChatOperationCode.SendPrivate:
                default:
                    if ((operationResponse.ReturnCode != 0) && (this.LogLevelClient >= LogLevel.Error))
                    {
                        if (operationResponse.ReturnCode == -2)
                        {
                            this.listener.DebugReturn(LogLevel.Error, string.Format("Chat Operation {0} failed on server. Message by server: {1}", operationResponse.OperationCode, operationResponse.DebugMessage));
                        }
                        else
                        {
                            this.listener.DebugReturn(LogLevel.Error, string.Format("Chat Operation {0} failed (Code: {1}). Debug Message: {2}", operationResponse.OperationCode, operationResponse.ReturnCode, operationResponse.DebugMessage));
                        }
                    }
                    break;
            }
        }

        void IPhotonPeerListener.OnStatusChanged(StatusCode statusCode)
        {
            switch (statusCode)
            {
                case StatusCode.Connect:
                    if (!this.IsProtocolSecure)
                    {
                        if (!this.Peer.EstablishEncryption())
                        {
                            if (this.LogLevelClient >= LogLevel.Error)
                            {
                                this.listener.DebugReturn(LogLevel.Error, "Error establishing encryption");
                            }
                        }
                    }
                    else
                    {
                        this.TryAuthenticateOnNameServer();
                    }

                    if (this.State == ChatState.ConnectingToNameServer)
                    {
                        this.State = ChatState.ConnectedToNameServer;
                        this.listener.OnChatStateChange(this.State);
                    }
                    else if (this.State == ChatState.ConnectingToFrontEnd)
                    {
                        if (!this.AuthenticateOnFrontEnd())
                        {
                            if (this.LogLevelClient >= LogLevel.Error)
                            {
                                this.listener.DebugReturn(LogLevel.Error, string.Format("Error authenticating on frontend! Check log output, AuthValues and if you're connected. State: {0}", this.State));
                            }
                        }
                    }
                    break;
                case StatusCode.EncryptionEstablished:
                    // once encryption is available, the client should send one (secure) authenticate. it includes the AppId (which identifies your app on the Photon Cloud)
                    this.TryAuthenticateOnNameServer();
                    break;
                case StatusCode.Disconnect:
                    switch (this.State)
                    {
                        case ChatState.ConnectWithFallbackProtocol:
                            this.AppSettings.EnableProtocolFallback = false;        // the client does a fallback only one time
                            this.NameServerPortOverride = 0;   // resets a value in the peer only (as we change the protocol, the port has to change, too)
                            this.Peer.TransportProtocol = (this.Peer.TransportProtocol == ConnectionProtocol.Tcp) ? ConnectionProtocol.Udp : ConnectionProtocol.Tcp;
                            this.ConnectIntern();

                            // the client now has to return, instead of break, to avoid further processing of the disconnect call
                            return;

                        case ChatState.Authenticated:
                            this.ConnectToFrontEnd();
                            // client disconnected from nameserver after authentication
                            // to switch to frontend
                            return;
                        case ChatState.Disconnecting:
                            // expected disconnect

                            if (this.stateTimer != null)
                            {
                                this.stateTimer.Dispose();
                                this.stateTimer = null;
                            }
                            break;
                        default:
                            // unexpected disconnect, we log warning and stacktrace
                            string stacktrace = string.Empty;
                            #if DEBUG
                            stacktrace = new System.Diagnostics.StackTrace(true).ToString();
                            #endif
                            this.listener.DebugReturn(LogLevel.Warning, $"Got an unexpected Disconnect in ChatState: {this.State}. DisconnectedCause: {this.DisconnectedCause}. Server: {this.Peer.ServerAddress} Trace: {stacktrace}");

                            if (this.stateTimer != null)
                            {
                                this.stateTimer.Dispose();
                                this.stateTimer = null;
                            }
                            break;
                    }
                    if (this.AuthValues != null)
                    {
                        this.AuthValues.Token = null; // when leaving the server, invalidate the secret (but not the auth values)
                    }
                    this.State = ChatState.Disconnected;
                    this.listener.OnChatStateChange(ChatState.Disconnected);
                    this.listener.OnDisconnected();
                    break;
                case StatusCode.DisconnectByServerUserLimit:
                    this.listener.DebugReturn(LogLevel.Error, "This connection was rejected due to the apps CCU limit.");
                    this.Disconnect(ChatDisconnectCause.MaxCcuReached);
                    break;
                case StatusCode.DnsExceptionOnConnect:
                    this.Disconnect(ChatDisconnectCause.DnsExceptionOnConnect);
                    break;
                case StatusCode.ServerAddressInvalid:
                    this.Disconnect(ChatDisconnectCause.ServerAddressInvalid);
                    break;
                case StatusCode.ExceptionOnConnect:
                case StatusCode.SecurityExceptionOnConnect:
                case StatusCode.EncryptionFailedToEstablish:
                    this.DisconnectedCause = ChatDisconnectCause.ExceptionOnConnect;

                    // if enabled, the client can attempt to connect with another networking-protocol to check if that connects
                    if (this.AppSettings.EnableProtocolFallback && this.State == ChatState.ConnectingToNameServer)
                    {
                        this.State = ChatState.ConnectWithFallbackProtocol;
                    }
                    else
                    {
                        this.Disconnect(ChatDisconnectCause.ExceptionOnConnect);
                    }

                    break;
                case StatusCode.Exception:
                case StatusCode.ExceptionOnReceive:
                    this.Disconnect(ChatDisconnectCause.Exception);
                    break;
                case StatusCode.DisconnectByServerTimeout:
                    this.Disconnect(ChatDisconnectCause.ServerTimeout);
                    break;
                case StatusCode.DisconnectByServerLogic:
                    this.Disconnect(ChatDisconnectCause.DisconnectByServerLogic);
                    break;
                case StatusCode.DisconnectByServerReasonUnknown:
                    this.Disconnect(ChatDisconnectCause.DisconnectByServerReasonUnknown);
                    break;
                case StatusCode.TimeoutDisconnect:
                    this.DisconnectedCause = ChatDisconnectCause.ClientTimeout;

                    // if enabled, the client can attempt to connect with another networking-protocol to check if that connects
                    if (this.AppSettings.EnableProtocolFallback && this.State == ChatState.ConnectingToNameServer)
                    {
                        this.State = ChatState.ConnectWithFallbackProtocol;
                    }
                    else
                    {
                        this.Disconnect(ChatDisconnectCause.ClientTimeout);
                    }
                    break;
            }
        }


        /// <summary>Callback for raw messages. Check documentation in interface.</summary>
        void IPhotonPeerListener.OnMessage(bool isRawMessage, object msg)
        {
            //string channelName = null;
            //var receivedBytes = (byte[])msg;
            //var channelId = BitConverter.ToInt32(receivedBytes, 0);
            //var messageBytes = new byte[receivedBytes.Length - 4];
            //Array.Copy(receivedBytes, 4, messageBytes, 0, receivedBytes.Length - 4);

            //foreach (var channel in this.PublicChannels)
            //{
            //    if (channel.Value.ChannelID == channelId)
            //    {
            //        channelName = channel.Key;
            //        break;
            //    }
            //}

            //if (channelName != null)
            //{
            //    this.listener.DebugReturn(LogLevel.Debug, string.Format("got OnMessage in channel {0}", channelName));
            //}
            //else
            //{
            //    this.listener.DebugReturn(LogLevel.Warning, string.Format("got OnMessage in unknown channel {0}", channelId));
            //}

            //this.listener.OnReceiveBroadcastMessage(channelName, messageBytes);
        }


        /// <summary>Called when the client received a Disconnect Message from the server. Signals an error and provides a message to debug the case.</summary>
        public void OnDisconnectMessage(DisconnectMessage obj)
        {
            this.listener.DebugReturn(LogLevel.Error, string.Format("OnDisconnectMessage. Code: {0} Msg: \"{1}\".", obj.Code, obj.DebugMessage));
            this.Disconnect(ChatDisconnectCause.DisconnectByDisconnectMessage);
        }


        #endregion

        private void TryAuthenticateOnNameServer()
        {
            if (!this.didAuthenticate)
            {
                this.didAuthenticate = this.AuthenticateOnNameServer(this.AppSettings.AppIdChat, this.AppSettings.AppVersion, this.FixedRegionOrDefault, this.AuthValues);
                if (!this.didAuthenticate)
                {
                    if (this.LogLevelClient >= LogLevel.Error)
                    {
                        this.listener.DebugReturn(LogLevel.Error, string.Format("Error calling OpAuthenticate! Did not work on NameServer. Check log output, AuthValues and if you're connected. State: {0}", this.State));
                    }
                }
            }
        }

        private bool SendChannelOperation(string[] channels, byte operation, int historyLength)
        {
            ParameterDictionary opParameters = new ParameterDictionary()
                                               { { (byte)ChatParameterCode.Channels, channels } };

            if (historyLength != 0)
            {
                opParameters.Add((byte)ChatParameterCode.HistoryLength, historyLength);
            }

            return this.Peer.SendOperation(operation, opParameters, SendOptions.SendReliable);
        }

        private void HandlePrivateMessageEvent(EventData eventData)
        {
            //Console.WriteLine(SupportClass.DictionaryToString(eventData.Parameters));

            object message = (object)eventData.Parameters[(byte)ChatParameterCode.Message];
            string sender = (string)eventData.Parameters[(byte)ChatParameterCode.Sender];
            int msgId = (int)eventData.Parameters[ChatParameterCode.MsgId];

            string channelName;
            if (this.UserId != null && this.UserId.Equals(sender))
            {
                string target = (string)eventData.Parameters[(byte)ChatParameterCode.UserId];
                channelName = this.GetPrivateChannelNameByUser(target);
            }
            else
            {
                channelName = this.GetPrivateChannelNameByUser(sender);
            }

            ChatChannel channel;
            if (!this.PrivateChannels.TryGetValue(channelName, out channel))
            {
                channel = new ChatChannel(channelName);
                channel.IsPrivate = true;
                channel.MessageLimit = this.MessageLimit;
                this.PrivateChannels.Add(channel.Name, channel);
            }

            channel.Add(sender, message, msgId);
            this.listener.OnPrivateMessage(sender, message, channelName);
        }

        private void HandleChatMessagesEvent(EventData eventData)
        {
            object[] messages = (object[])eventData.Parameters[(byte)ChatParameterCode.Messages];
            string[] senders = (string[])eventData.Parameters[(byte)ChatParameterCode.Senders];
            string channelName = (string)eventData.Parameters[(byte)ChatParameterCode.Channel];
            int lastMsgId = (int)eventData.Parameters[ChatParameterCode.MsgId];

            ChatChannel channel;
            if (!this.PublicChannels.TryGetValue(channelName, out channel))
            {
                if (this.LogLevelClient >= LogLevel.Warning)
                {
                    this.listener.DebugReturn(LogLevel.Warning, "Channel " + channelName + " for incoming message event not found.");
                }
                return;
            }

            channel.Add(senders, messages, lastMsgId);
            this.listener.OnGetMessages(channelName, senders, messages);
        }

        private void HandleSubscribeEvent(EventData eventData)
        {
            string[] channelsInResponse = (string[])eventData.Parameters[ChatParameterCode.Channels];
            bool[] results = (bool[])eventData.Parameters[ChatParameterCode.SubscribeResults];
            for (int i = 0; i < channelsInResponse.Length; i++)
            {
                if (results[i])
                {
                    string channelName = channelsInResponse[i];
                    ChatChannel channel;
                    if (!this.PublicChannels.TryGetValue(channelName, out channel))
                    {
                        channel = new ChatChannel(channelName);
                        channel.MessageLimit = this.MessageLimit;
                        this.PublicChannels.Add(channel.Name, channel);
                    }
                    object temp;
                    if (eventData.Parameters.TryGetValue(ChatParameterCode.Properties, out temp))
                    {
                        Dictionary<object, object> channelProperties = temp as Dictionary<object, object>;
                        channel.ReadChannelProperties(channelProperties);
                    }
                    if (channel.PublishSubscribers) // or maybe remove check & always add anyway?
                    {
                        channel.AddSubscriber(this.UserId);
                    }
                    if (eventData.Parameters.TryGetValue(ChatParameterCode.ChannelSubscribers, out temp))
                    {
                        string[] subscribers = temp as string[];
                        channel.AddSubscribers(subscribers);
                    }
                    #if CHAT_EXTENDED
                    if (eventData.Parameters.TryGetValue(ChatParameterCode.UserProperties, out temp))
                    {
                        //UnityEngine.Debug.LogFormat("temp = {0}", temp);
                        Dictionary<string, object> userProperties = temp as Dictionary<string, object>;
                        foreach (var pair in userProperties)
                        {
                            channel.ReadUserProperties(pair.Key, pair.Value as Dictionary<object, object>);
                        }
                    }
                    #endif
                }
            }

            this.listener.OnSubscribed(channelsInResponse, results);
        }

        private void HandleUnsubscribeEvent(EventData eventData)
        {
            string[] channelsInRequest = (string[])eventData[ChatParameterCode.Channels];
            for (int i = 0; i < channelsInRequest.Length; i++)
            {
                string channelName = channelsInRequest[i];
                this.PublicChannels.Remove(channelName);
                this.PublicChannelsUnsubscribing.Remove(channelName);
            }

            this.listener.OnUnsubscribed(channelsInRequest);
        }

        private void HandleAuthResponse(OperationResponse operationResponse)
        {
            if (this.LogLevelClient >= LogLevel.Info)
            {
                this.listener.DebugReturn(LogLevel.Info, operationResponse.ToStringFull() + " on: " + this.CurrentServerAddress);
            }

            if (operationResponse.ReturnCode == 0)
            {
                if (this.State == ChatState.ConnectedToNameServer)
                {
                    this.State = ChatState.Authenticated;
                    this.listener.OnChatStateChange(this.State);

                    if (operationResponse.Parameters.ContainsKey(ChatParameterCode.Secret))
                    {
                        if (this.AuthValues == null)
                        {
                            this.AuthValues = new AuthenticationValues();
                        }
                        this.AuthValues.Token = operationResponse[ChatParameterCode.Secret];

                        this.FrontendAddress = (string)operationResponse[ChatParameterCode.Address];

                        // we disconnect and status handler starts to connect to front end
                        this.Peer.Disconnect();
                    }
                    else
                    {
                        if (this.LogLevelClient >= LogLevel.Error)
                        {
                            this.listener.DebugReturn(LogLevel.Error, "No secret in authentication response.");
                        }
                    }
                    if (operationResponse.Parameters.ContainsKey(ChatParameterCode.UserId))
                    {
                        string incomingId = operationResponse.Parameters[ChatParameterCode.UserId] as string;
                        if (!string.IsNullOrEmpty(incomingId))
                        {
                            this.UserId = incomingId;
                            this.listener.DebugReturn(LogLevel.Info, string.Format("Received your UserID from server. Updating local value to: {0}", this.UserId));
                        }
                    }
                }
                else if (this.State == ChatState.ConnectingToFrontEnd)
                {
                    this.State = ChatState.ConnectedToFrontEnd;
                    this.listener.OnChatStateChange(this.State);
                    this.listener.OnConnected();
                }

                // optionally, OpAuth may return some data for the client to use. if it's available, call OnCustomAuthenticationResponse
                Dictionary<string, object> data = (Dictionary<string, object>)operationResponse[ChatParameterCode.Data];
                if (data != null)
                {
                    this.listener.OnCustomAuthenticationResponse(data);
                }
            }
            else
            {
                //this.listener.DebugReturn(LogLevel.Info, operationResponse.ToStringFull() + " NS: " + this.NameServerAddress + " FrontEnd: " + this.frontEndAddress);

                switch (operationResponse.ReturnCode)
                {
                    case ErrorCode.InvalidAuthentication:
                        this.DisconnectedCause = ChatDisconnectCause.InvalidAuthentication;
                        break;
                    case ErrorCode.CustomAuthenticationFailed:
                        this.DisconnectedCause = ChatDisconnectCause.CustomAuthenticationFailed;
                        this.listener.OnCustomAuthenticationFailed(operationResponse.DebugMessage);
                        break;
                    case ErrorCode.InvalidRegion:
                        this.DisconnectedCause = ChatDisconnectCause.InvalidRegion;
                        break;
                    case ErrorCode.MaxCcuReached:
                        this.DisconnectedCause = ChatDisconnectCause.MaxCcuReached;
                        break;
                    case ErrorCode.OperationNotAllowedInCurrentState:
                        this.DisconnectedCause = ChatDisconnectCause.OperationNotAllowedInCurrentState;
                        break;
                    case ErrorCode.AuthenticationTicketExpired:
                        this.DisconnectedCause = ChatDisconnectCause.AuthenticationTicketExpired;
                        break;
                }

                if (this.LogLevelClient >= LogLevel.Error)
                {
                    this.listener.DebugReturn(LogLevel.Error, string.Format("{0} ClientState: {1} ServerAddress: {2}", operationResponse.ToStringFull(), this.State, this.Peer.ServerAddress));
                }


                this.Disconnect(this.DisconnectedCause);
            }
        }

        private void HandleStatusUpdate(EventData eventData)
        {
            string user = (string)eventData.Parameters[ChatParameterCode.Sender];
            int status = (int)eventData.Parameters[ChatParameterCode.Status];

            object message = null;
            bool gotMessage = eventData.Parameters.ContainsKey(ChatParameterCode.Message);
            if (gotMessage)
            {
                message = eventData.Parameters[ChatParameterCode.Message];
            }

            this.listener.OnStatusUpdate(user, status, gotMessage, message);
        }

        private bool ConnectToFrontEnd()
        {
            this.State = ChatState.ConnectingToFrontEnd;

            if (this.LogLevelClient >= LogLevel.Info)
            {
                this.listener.DebugReturn(LogLevel.Info, "Connecting to frontend " + this.FrontendAddress);
            }

            #if UNITY_WEBGL
            if (this.TransportProtocol == ConnectionProtocol.Tcp || this.TransportProtocol == ConnectionProtocol.Udp)
            {
                this.listener.DebugReturn(LogLevel.Warning, "WebGL requires WebSockets. Switching TransportProtocol to WebSocketSecure.");
                this.TransportProtocol = ConnectionProtocol.WebSocketSecure;
            }
            #endif

            if (!this.Peer.Connect(this.FrontendAddress, this.AppSettings.AppIdChat, this.AuthValues.Token, proxyServerAddress: this.AppSettings.ProxyServer))
            {
                if (this.LogLevelClient >= LogLevel.Error)
                {
                    this.listener.DebugReturn(LogLevel.Error, string.Format("Connecting to frontend {0} failed.", this.FrontendAddress));
                }
                return false;
            }

            return true;
        }

        private bool AuthenticateOnFrontEnd()
        {
            // TODO: implement AuthOnce
            //this.listener.DebugReturn(LogLevel.Error, "DEBUG: We do not send auth to Frontend now.");
            //return true;

            if (this.AuthValues != null)
            {
                if (this.AuthValues.Token == null)
                {
                    if (this.LogLevelClient >= LogLevel.Error)
                    {
                        this.listener.DebugReturn(LogLevel.Error, "Can't authenticate on front end server. Secret (AuthValues.Token) is not set");
                    }
                    return false;
                }
                else
                {
                    ParameterDictionary opParameters = new ParameterDictionary { { (byte)ChatParameterCode.Secret, this.AuthValues.Token } };
                    if (this.PrivateChatHistoryLength > -1)
                    {
                        opParameters[(byte)ChatParameterCode.HistoryLength] = this.PrivateChatHistoryLength;
                    }

                    return this.Peer.SendOperation(ChatOperationCode.Authenticate, opParameters, SendOptions.SendReliable);
                }
            }
            else
            {
                if (this.LogLevelClient >= LogLevel.Error)
                {
                    this.listener.DebugReturn(LogLevel.Error, "Can't authenticate on front end server. Authentication Values are not set");
                }
                return false;
            }
        }

        private void HandleUserUnsubscribedEvent(EventData eventData)
        {
            string channelName = eventData.Parameters[ChatParameterCode.Channel] as string;
            string userId = eventData.Parameters[ChatParameterCode.UserId] as string;
            ChatChannel channel;
            if (this.PublicChannels.TryGetValue(channelName, out channel))
            {
                if (!channel.PublishSubscribers)
                {
                    if (this.LogLevelClient >= LogLevel.Warning)
                    {
                        this.listener.DebugReturn(LogLevel.Warning, string.Format("Channel \"{0}\" for incoming UserUnsubscribed (\"{1}\") event does not have PublishSubscribers enabled.", channelName, userId));
                    }
                }
                if (!channel.RemoveSubscriber(userId)) // user not found!
                {
                    if (this.LogLevelClient >= LogLevel.Warning)
                    {
                        this.listener.DebugReturn(LogLevel.Warning, string.Format("Channel \"{0}\" does not contain unsubscribed user \"{1}\".", channelName, userId));
                    }
                }
            }
            else
            {
                if (this.LogLevelClient >= LogLevel.Warning)
                {
                    this.listener.DebugReturn(LogLevel.Warning, string.Format("Channel \"{0}\" not found for incoming UserUnsubscribed (\"{1}\") event.", channelName, userId));
                }
            }
            this.listener.OnUserUnsubscribed(channelName, userId);
        }

        private void HandleUserSubscribedEvent(EventData eventData)
        {
            string channelName = eventData.Parameters[ChatParameterCode.Channel] as string;
            string userId = eventData.Parameters[ChatParameterCode.UserId] as string;
            ChatChannel channel;
            if (this.PublicChannels.TryGetValue(channelName, out channel))
            {
                if (!channel.PublishSubscribers)
                {
                    if (this.LogLevelClient >= LogLevel.Warning)
                    {
                        this.listener.DebugReturn(LogLevel.Warning, string.Format("Channel \"{0}\" for incoming UserSubscribed (\"{1}\") event does not have PublishSubscribers enabled.", channelName, userId));
                    }
                }
                if (!channel.AddSubscriber(userId)) // user came back from the dead ?
                {
                    if (this.LogLevelClient >= LogLevel.Warning)
                    {
                        this.listener.DebugReturn(LogLevel.Warning, string.Format("Channel \"{0}\" already contains newly subscribed user \"{1}\".", channelName, userId));
                    }
                }
                else if (channel.MaxSubscribers > 0 && channel.Subscribers.Count > channel.MaxSubscribers)
                {
                    if (this.LogLevelClient >= LogLevel.Warning)
                    {
                        this.listener.DebugReturn(LogLevel.Warning, string.Format("Channel \"{0}\"'s MaxSubscribers exceeded. count={1} > MaxSubscribers={2}.", channelName, channel.Subscribers.Count, channel.MaxSubscribers));
                    }
                }
                #if CHAT_EXTENDED
                object temp;
                if (eventData.Parameters.TryGetValue(ChatParameterCode.UserProperties, out temp))
                {
                    Dictionary<object, object> userProperties = temp as Dictionary<object, object>;
                    channel.ReadUserProperties(userId, userProperties);
                }
                #endif
            }
            else
            {
                if (this.LogLevelClient >= LogLevel.Warning)
                {
                    this.listener.DebugReturn(LogLevel.Warning, string.Format("Channel \"{0}\" not found for incoming UserSubscribed (\"{1}\") event.", channelName, userId));
                }
            }
            this.listener.OnUserSubscribed(channelName, userId);
        }


        /// <summary>Name Server Host Name for Photon Cloud. Without port and without any prefix.</summary>
        public string NameServerHost = "ns.photonengine.io";

        /// <summary>Name Server Address for Photon Cloud (based on current protocol). You can use the default values and usually won't have to set this value.</summary>
        public string NameServerAddress { get { return this.GetNameServerAddress(); } }

        /// <summary>Name Server port per protocol (the UDP port is different from the TCP port, etc).</summary>
        private static readonly Dictionary<ConnectionProtocol, int> ProtocolToNameServerPort = new Dictionary<ConnectionProtocol, int>() { { ConnectionProtocol.Udp, 5058 }, { ConnectionProtocol.Tcp, 4533 }, { ConnectionProtocol.WebSocket, 9093 }, { ConnectionProtocol.WebSocketSecure, 19093 } }; //, { ConnectionProtocol.RHttp, 6063 } };

        /// <summary>If not zero, this is used for the name server port on connect. Independent of protocol (so this better matches). Set by ChatClient.ConnectUsingSettings.</summary>
        /// <remarks>This is reset when the protocol fallback is used.</remarks>
        public ushort NameServerPortOverride;


        internal virtual bool IsProtocolSecure { get { return this.TransportProtocol == ConnectionProtocol.WebSocketSecure; } }



        // Sets up the socket implementations to use, depending on platform
        [System.Diagnostics.Conditional("SUPPORTED_UNITY")]
        private void ConfigUnitySockets()
        {
            Type websocketType = null;
            #if (UNITY_XBOXONE || UNITY_GAMECORE) && !UNITY_EDITOR
            websocketType = Type.GetType("ExitGames.Client.Photon.SocketNativeSource, Assembly-CSharp", false);
            if (websocketType == null)
            {
                websocketType = Type.GetType("ExitGames.Client.Photon.SocketNativeSource, Assembly-CSharp-firstpass", false);
            }
            if (websocketType == null)
            {
                websocketType = Type.GetType("ExitGames.Client.Photon.SocketNativeSource, PhotonRealtime", false);
            }
            if (websocketType != null)
            {
                this.SocketImplementationConfig[ConnectionProtocol.Udp] = websocketType;    // on Xbox, the native socket plugin supports UDP as well
            }
            #else
            // to support WebGL export in Unity, we find and assign the SocketWebTcp class (if it's in the project).
            // alternatively class SocketWebTcp might be in the Photon3Unity3D.dll
            websocketType = Type.GetType("Photon.Client.SocketWebTcp, PhotonWebSocket", false);
            if (websocketType == null)
            {
                websocketType = Type.GetType("Photon.Client.SocketWebTcp, Assembly-CSharp-firstpass", false);
            }
            if (websocketType == null)
            {
                websocketType = Type.GetType("Photon.Client.SocketWebTcp, Assembly-CSharp", false);
            }
            #endif

            if (websocketType != null)
            {
                this.SocketImplementationConfig[ConnectionProtocol.WebSocket] = websocketType;
                this.SocketImplementationConfig[ConnectionProtocol.WebSocketSecure] = websocketType;
            }

            //#if NET_4_6 && (UNITY_EDITOR || !ENABLE_IL2CPP)
            //this.SocketImplementationConfig[ConnectionProtocol.Udp] = typeof(SocketUdpAsync);
            //this.SocketImplementationConfig[ConnectionProtocol.Tcp] = typeof(SocketTcpAsync);
            //#endif
        }


        /// <summary>
        /// Gets the NameServer Address (with prefix and port), based on the set protocol (this.UsedProtocol).
        /// </summary>
        /// <returns>NameServer Address (with prefix and port).</returns>
        private string GetNameServerAddress()
        {
            var protocolPort = 0;
            ProtocolToNameServerPort.TryGetValue(this.TransportProtocol, out protocolPort);

            if (this.NameServerPortOverride != 0)
            {
                this.listener.DebugReturn(LogLevel.Info, string.Format("Using NameServerPortInAppSettings as port for Name Server: {0}", this.NameServerPortOverride));
                protocolPort = this.NameServerPortOverride;
            }

            switch (this.TransportProtocol)
            {
                case ConnectionProtocol.Udp:
                case ConnectionProtocol.Tcp:
                    return string.Format("{0}:{1}", NameServerHost, protocolPort);
                case ConnectionProtocol.WebSocket:
                    return string.Format("ws://{0}:{1}", NameServerHost, protocolPort);
                case ConnectionProtocol.WebSocketSecure:
                    return string.Format("wss://{0}:{1}", NameServerHost, protocolPort);
                default:
                    throw new ArgumentOutOfRangeException();
            }
        }


        /// <summary> Authenticates on NameServer. </summary>
        /// <returns>If the authentication operation request could be sent.</returns>
        protected internal bool AuthenticateOnNameServer(string appId, string appVersion, string region, AuthenticationValues authValues)
        {
            if (this.LogLevelClient >= LogLevel.Info)
            {
                this.listener.DebugReturn(LogLevel.Info, "OpAuthenticate()");
            }

            ParameterDictionary opParameters = new ParameterDictionary();

            opParameters[ChatParameterCode.AppVersion] = appVersion;
            opParameters[ChatParameterCode.ApplicationId] = appId;
            opParameters[ChatParameterCode.Region] = region;

            //opParameters[193] = (byte)0;  // encryption mode
            //opParameters[195] = (byte)0;  // expected protocol

            if (authValues != null)
            {
                if (!string.IsNullOrEmpty(authValues.UserId))
                {
                    opParameters[ChatParameterCode.UserId] = authValues.UserId;
                }

                if (authValues.AuthType != CustomAuthenticationType.None)
                {
                    opParameters[ChatParameterCode.ClientAuthenticationType] = (byte) authValues.AuthType;
                    if (authValues.Token != null)
                    {
                        opParameters[ChatParameterCode.Secret] = authValues.Token;
                    }
                    else
                    {
                        if (!string.IsNullOrEmpty(authValues.AuthGetParameters))
                        {
                            opParameters[ChatParameterCode.ClientAuthenticationParams] = authValues.AuthGetParameters;
                        }
                        if (authValues.AuthPostData != null)
                        {
                            opParameters[ChatParameterCode.ClientAuthenticationData] = authValues.AuthPostData;
                        }
                    }
                }
            }

            return this.Peer.SendOperation(ChatOperationCode.Authenticate, opParameters, new SendOptions() { Reliability = true, Encrypt = true });
        }




        #endregion


        #if CHAT_EXTENDED

        internal bool SetChannelProperties(string channelName, Dictionary<object, object> channelProperties, Dictionary<object, object> expectedProperties = null, bool httpForward = false)
        {
            if (!this.CanChat)
            {
                this.listener.DebugReturn(LogLevel.Error, "SetChannelProperties called while not connected to front end server.");
                return false;
            }

            if (string.IsNullOrEmpty(channelName) || channelProperties == null || channelProperties.Count == 0)
            {
                this.listener.DebugReturn(LogLevel.Warning, "SetChannelProperties parameters must be non-null and not empty.");
                return false;
            }
            Dictionary<byte, object> parameters = new Dictionary<byte, object>
                                                  {
                                                      { ChatParameterCode.Channel, channelName },
                                                      { ChatParameterCode.Properties, channelProperties },
                                                      { ChatParameterCode.Broadcast, true }
                                                  };
            if (httpForward)
            {
                parameters.Add(ChatParameterCode.WebFlags, HttpForwardWebFlag);
            }
            if (expectedProperties != null && expectedProperties.Count > 0)
            {
                parameters.Add(ChatParameterCode.ExpectedValues, expectedProperties);
            }
            return this.Peer.SendOperation(ChatOperationCode.SetProperties, parameters, SendOptions.SendReliable);
        }

        public bool SetCustomChannelProperties(string channelName, Dictionary<string, object> channelProperties, Dictionary<string, object> expectedProperties = null, bool httpForward = false)
        {
            if (channelProperties != null && channelProperties.Count > 0)
            {
                Dictionary<object, object> properties = new Dictionary<object, object>(channelProperties.Count);
                foreach (var pair in channelProperties)
                {
                    properties.Add(pair.Key, pair.Value);
                }
                Dictionary<object, object> expected = null;
                if (expectedProperties != null && expectedProperties.Count > 0)
                {
                    expected = new Dictionary<object, object>(expectedProperties.Count);
                    foreach (var pair in expectedProperties)
                    {
                        expected.Add(pair.Key, pair.Value);
                    }
                }
                return this.SetChannelProperties(channelName, properties, expected, httpForward);
            }
            return this.SetChannelProperties(channelName, null);
        }

        public bool SetCustomUserProperties(string channelName, string userId, Dictionary<string, object> userProperties, Dictionary<string, object> expectedProperties = null, bool httpForward = false)
        {
            if (userProperties != null && userProperties.Count > 0)
            {
                Dictionary<object, object> properties = new Dictionary<object, object>(userProperties.Count);
                foreach (var pair in userProperties)
                {
                    properties.Add(pair.Key, pair.Value);
                }
                Dictionary<object, object> expected = null;
                if (expectedProperties != null && expectedProperties.Count > 0)
                {
                    expected = new Dictionary<object, object>(expectedProperties.Count);
                    foreach (var pair in expectedProperties)
                    {
                        expected.Add(pair.Key, pair.Value);
                    }
                }
                return this.SetUserProperties(channelName, userId, properties, expected, httpForward);
            }
            return this.SetUserProperties(channelName, userId, null);
        }

        internal bool SetUserProperties(string channelName, string userId, Dictionary<object, object> channelProperties, Dictionary<object, object> expectedProperties = null, bool httpForward = false)
        {
            if (!this.CanChat)
            {
                this.listener.DebugReturn(LogLevel.Error, "SetUserProperties called while not connected to front end server.");
                return false;
            }
            if (string.IsNullOrEmpty(channelName))
            {
                this.listener.DebugReturn(LogLevel.Warning, "SetUserProperties \"channelName\" parameter must be non-null and not empty.");
                return false;
            }
            if (channelProperties == null || channelProperties.Count == 0)
            {
                this.listener.DebugReturn(LogLevel.Warning, "SetUserProperties \"channelProperties\" parameter must be non-null and not empty.");
                return false;
            }
            if (string.IsNullOrEmpty(userId))
            {
                this.listener.DebugReturn(LogLevel.Warning, "SetUserProperties \"userId\" parameter must be non-null and not empty.");
                return false;
            }
            Dictionary<byte, object> parameters = new Dictionary<byte, object>
                                                  {
                                                      { ChatParameterCode.Channel, channelName },
                                                      { ChatParameterCode.Properties, channelProperties },
                                                      { ChatParameterCode.UserId, userId },
                                                      { ChatParameterCode.Broadcast, true }
                                                  };
            if (httpForward)
            {
                parameters.Add(ChatParameterCode.WebFlags, HttpForwardWebFlag);
            }
            if (expectedProperties != null && expectedProperties.Count > 0)
            {
                parameters.Add(ChatParameterCode.ExpectedValues, expectedProperties);
            }
            return this.Peer.SendOperation(ChatOperationCode.SetProperties, parameters, SendOptions.SendReliable);
        }

        private void HandlePropertiesChanged(EventData eventData)
        {
            string channelName = eventData.Parameters[ChatParameterCode.Channel] as string;
            ChatChannel channel;
            if (!this.PublicChannels.TryGetValue(channelName, out channel))
            {
                this.listener.DebugReturn(LogLevel.Warning, string.Format("Channel {0} for incoming ChannelPropertiesUpdated event not found.", channelName));
                return;
            }
            string senderId = eventData.Parameters[ChatParameterCode.Sender] as string;
            Dictionary<object, object> changedProperties = eventData.Parameters[ChatParameterCode.Properties] as Dictionary<object, object>;
            object temp;
            if (eventData.Parameters.TryGetValue(ChatParameterCode.UserId, out temp))
            {
                string targetUserId = temp as string;
                channel.ReadUserProperties(targetUserId, changedProperties);
                this.listener.OnUserPropertiesChanged(channelName, targetUserId, senderId, changedProperties);
            }
            else
            {
                channel.ReadChannelProperties(changedProperties);
                this.listener.OnChannelPropertiesChanged(channelName, senderId, changedProperties);
            }
        }

        private void HandleErrorInfoEvent(EventData eventData)
        {
            string channel = eventData.Parameters[ChatParameterCode.Channel] as string;
            string msg = eventData.Parameters[ChatParameterCode.DebugMessage] as string;
            object data = eventData.Parameters[ChatParameterCode.DebugData];
            this.listener.OnErrorInfo(channel, msg, data);
        }

        #endif
    }
}
