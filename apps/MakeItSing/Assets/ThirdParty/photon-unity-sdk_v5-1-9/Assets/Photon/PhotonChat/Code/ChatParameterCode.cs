// ----------------------------------------------------------------------------------------------------------------------
// <summary>The Photon Chat Api enables clients to connect to a chat server and communicate with other clients.</summary>
// <remarks>ChatClient is the main class of this api.</remarks>
// <copyright company="Exit Games GmbH">Photon Chat Api - Copyright (C) 2014 Exit Games GmbH</copyright>
// ----------------------------------------------------------------------------------------------------------------------

namespace Photon.Chat
{
    /// <summary>Class for constants. Codes for parameters of Operations and Events.</summary>
    /// <remarks>
    /// Realtime and Chat use the same Name Server operations.
    /// This partial class contains any values shared with Realtime.
    /// </remarks>
    public partial class ChatParameterCode
    {
        /// <summary>(224) Your application's ID: a name on your own Photon or a GUID on the Photon Cloud</summary>
        public const byte ApplicationId = 224;
        /// <summary>(221) Internally used to establish encryption</summary>
        public const byte Secret = 221;
        /// <summary>(220) Version of your application</summary>
        public const byte AppVersion = 220;
        /// <summary>(217) This key's (byte) value defines the target custom authentication type/service the client connects with. Used in OpAuthenticate</summary>
        public const byte ClientAuthenticationType = 217;
        /// <summary>(216) This key's (string) value provides parameters sent to the custom authentication type/service the client connects with. Used in OpAuthenticate</summary>
        public const byte ClientAuthenticationParams = 216;
        /// <summary>(214) This key's (string or byte[]) value provides parameters sent to the custom authentication service setup in Photon Dashboard. Used in OpAuthenticate</summary>
        public const byte ClientAuthenticationData = 214;
        /// <summary>(210) Used for region values in OpAuth and OpGetRegions.</summary>
        public const byte Region = 210;
        /// <summary>(230) Address of a (game) server to use.</summary>
        public const byte Address = 230;
        /// <summary>(225) User's ID</summary>
        public const byte UserId = 225;
        /// <summary>(245) Code of "data". Used optionally in an OpAuthenticate response (among other uses).</summary>
        public const byte Data = (byte)245;
    }

    /// <summary>
    /// Wraps up codes for parameters (in operations and events) used internally in Photon Chat. You don't have to use them directly usually.
    /// </summary>
    public partial class ChatParameterCode
    {
        /// <summary>(0) Array of chat channels.</summary>
        public const byte Channels = 0;
        /// <summary>(1) Name of a single chat channel.</summary>
        public const byte Channel = 1;
        /// <summary>(2) Array of chat messages.</summary>
        public const byte Messages = 2;
        /// <summary>(3) A single chat message.</summary>
        public const byte Message = 3;
        /// <summary>(4) Array of names of the users who sent the array of chat messages.</summary>
        public const byte Senders = 4;
        /// <summary>(5) Name of a the user who sent a chat message.</summary>
        public const byte Sender = 5;
        /// <summary>(6) Not used.</summary>
        public const byte ChannelUserCount = 6;
        /// <summary>(8) Id of a message.</summary>
        public const byte MsgId = 8;
        /// <summary>(9) Not used.</summary>
        public const byte MsgIds = 9;
        /// <summary>(15) Subscribe operation result parameter. A bool[] with result per channel.</summary>
        public const byte SubscribeResults = 15;

        /// <summary>(10) Status</summary>
        public const byte Status = 10;
        /// <summary>(11) Friends</summary>
        public const byte Friends = 11;
        /// <summary>(12) SkipMessage is used in SetOnlineStatus and if true, the message is not being broadcast.</summary>
        public const byte SkipMessage = 12;

        /// <summary>(14) Number of message to fetch from history. 0: no history. 1 and higher: number of messages in history. -1: all history.</summary>
        public const byte HistoryLength = 14;


        /// <summary>(17) Debug string provided by server in some cases.</summary>
        public const byte DebugMessage = 17;

        /// <summary>(21) WebFlags object for changing behaviour of webhooks from client.</summary>
        public const byte WebFlags = 21;

        /// <summary>(22) WellKnown or custom properties of channel or user.</summary>
        /// <remarks>
        /// In event <see cref="ChatEventCode.Subscribe"/> it's always channel properties,
        /// in event <see cref="ChatEventCode.UserSubscribed"/> it's always user properties,
        /// in event <see cref="ChatEventCode.PropertiesChanged"/> it's channel properties unless <see cref="UserId"/> parameter value is not null
        /// </remarks>
        public const byte Properties = 22;
        /// <summary>(23) Array of UserIds of users already subscribed to a channel.</summary>
        /// <remarks>Used in Subscribe event when PublishSubscribers is enabled.
        /// Does not include local user who just subscribed.
        /// Maximum length is (<see cref="ChatChannel.MaxSubscribers"/> - 1).</remarks>
        public const byte ChannelSubscribers = 23;
        /// <summary>(24) Optional data sent in ErrorInfo event from Chat WebHooks. </summary>
        public const byte DebugData = 24;
        /// <summary>(25) Code for values to be used for "Check And Swap" (CAS) when changing properties.</summary>
        public const byte ExpectedValues = 25;
        /// <summary>(26) Code for broadcast parameter of <see cref="ChatOperationCode.SetProperties"/> method.</summary>
        public const byte Broadcast = 26;
        /// <summary>
        /// WellKnown and custom user properties. 
        /// </summary>
        /// <remarks>
        /// Used only in event <see cref="ChatEventCode.Subscribe"/>
        /// </remarks>
        public const byte UserProperties = 28;

        /// <summary>
        /// Generated unique reusable room id
        /// </summary>
        public const byte UniqueRoomId = 29;
    }
}