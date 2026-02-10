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
    using System.Diagnostics;
    using System.Collections.Generic;
    using Photon.Client;

    #if SUPPORTED_UNITY
    using SupportClass = Photon.Client.SupportClass;
    #endif


    /// <summary>
    /// Options for optional "Custom Authentication" services used with Photon. Used by OpAuthenticate after connecting to Photon.
    /// </summary>
    public enum CustomAuthenticationType : byte
    {
        /// <summary>Use a custom authentication service.</summary>
        Custom = 0,

        /// <summary>Authenticates users by their Steam Account. Set Steam's ticket as "ticket" via AddAuthParameter().</summary>
        Steam = 1,

        /// <summary>Authenticates users by their Facebook Account.  Set Facebook token as "token" via AddAuthParameter().</summary>
        Facebook = 2,

        /// <summary>Authenticates users by their Oculus Account and token. Set Oculus' userid as "userid" and nonce as "nonce" via AddAuthParameter().</summary>
        Oculus = 3,

        /// <summary>Authenticates users by their PSN Account and token on PS4. Set token as "token", env as "env" and userName as "userName" via AddAuthParameter().</summary>
        PlayStation4 = 4,

        /// <summary>Authenticates users by their Xbox Account. Pass the XSTS token via SetAuthPostData().</summary>
        Xbox = 5,

        /// <summary>Authenticates users by their HTC Viveport Account. Set userToken as "userToken" via AddAuthParameter().</summary>
        Viveport = 10,

        /// <summary>Authenticates users by their NSA ID. Set token as "token" and appversion as "appversion" via AddAuthParameter(). The appversion is optional.</summary>
        NintendoSwitch = 11,

        /// <summary>Authenticates users by their PSN Account and token on PS5. Set token as "token", env as "env" and userName as "userName" via AddAuthParameter().</summary>
        PlayStation5 = 12,

        /// <summary>Authenticates users with Epic Online Services (EOS). Set token as "token" and ownershipToken as "ownershipToken" via AddAuthParameter(). The ownershipToken is optional.</summary>
        Epic = 13,

        /// <summary>Authenticates users with Facebook Gaming api. Set token as "token" via AddAuthParameter().</summary>
        FacebookGaming = 15,

        /// <summary>Disables custom authentication. Same as not providing any AuthenticationValues for connect (more precisely for: OpAuthenticate).</summary>
        None = byte.MaxValue
    }


    /// <summary>
    /// Container for user authentication in Photon. Set AuthValues before you connect - all else is handled.
    /// </summary>
    /// <remarks>
    /// On Photon, user authentication is optional but can be useful in many cases.
    /// If you want to FindFriends, a unique ID per user is very practical.
    ///
    /// There are basically three options for user authentication: None at all, the client sets some UserId
    /// or you can use some account web-service to authenticate a user (and set the UserId server-side).
    ///
    /// Custom Authentication lets you verify end-users by some kind of login or token. It sends those
    /// values to Photon which will verify them before granting access or disconnecting the client.
    ///
    /// The AuthValues are sent in OpAuthenticate when you connect, so they must be set before you connect.
    /// If the AuthValues.UserId is null or empty when it's sent to the server, then the Photon Server assigns a UserId!
    ///
    /// The Photon Cloud Dashboard will let you enable this feature and set important server values for it.
    /// https://dashboard.photonengine.com
    /// </remarks>
    public class AuthenticationValues
    {
        /// <summary>See AuthType.</summary>
        private CustomAuthenticationType authType = CustomAuthenticationType.None;

        /// <summary>The type of authentication provider that should be used. Defaults to None (no auth whatsoever).</summary>
        /// <remarks>Several auth providers are available and CustomAuthenticationType.Custom can be used if you build your own service.</remarks>
        public CustomAuthenticationType AuthType
        {
            get { return authType; }
            set { authType = value; }
        }

        /// <summary>This string must contain any (http get) parameters expected by the used authentication service. By default, username and token.</summary>
        /// <remarks>
        /// Maps to operation parameter 216.
        /// Standard http get parameters are used here and passed on to the service that's defined in the server (Photon Cloud Dashboard).
        /// </remarks>
        public string AuthGetParameters { get; set; }

        /// <summary>Data to be passed-on to the auth service via POST. Default: null (not sent). Either string or byte[] (see setters).</summary>
        /// <remarks>Maps to operation parameter 214.</remarks>
        public object AuthPostData { get; private set; }

        /// <summary>Internal <b>Photon token</b>. After initial authentication, Photon provides a token for this client, subsequently used as (cached) validation.</summary>
        /// <remarks>Any token for custom authentication should be set via SetAuthPostData or AddAuthParameter.</remarks>
        public object Token { get; protected internal set; }

        /// <summary>The UserId should be a unique identifier per user. This is for finding friends, etc..</summary>
        /// <remarks>See remarks of AuthValues for info about how this is set and used.</remarks>
        public string UserId { get; set; }


        /// <summary>Creates empty auth values without any info.</summary>
        public AuthenticationValues()
        {
        }

        /// <summary>Creates minimal info about the user. If this is authenticated or not, depends on the set AuthType.</summary>
        /// <param name="userId">Some UserId to set in Photon.</param>
        public AuthenticationValues(string userId)
        {
            this.UserId = userId;
        }

        /// <summary>Sets the data to be passed-on to the auth service via POST.</summary>
        /// <remarks>AuthPostData is just one value. Each SetAuthPostData replaces any previous value. It can be either a string, a byte[] or a dictionary.</remarks>
        /// <param name="stringData">String data to be used in the body of the POST request. Null or empty string will set AuthPostData to null.</param>
        public virtual void SetAuthPostData(string stringData)
        {
            this.AuthPostData = (string.IsNullOrEmpty(stringData)) ? null : stringData;
        }

        /// <summary>Sets the data to be passed-on to the auth service via POST.</summary>
        /// <remarks>AuthPostData is just one value. Each SetAuthPostData replaces any previous value. It can be either a string, a byte[] or a dictionary.</remarks>
        /// <param name="byteData">Binary token / auth-data to pass on.</param>
        public virtual void SetAuthPostData(byte[] byteData)
        {
            this.AuthPostData = byteData;
        }

        /// <summary>Sets data to be passed-on to the auth service as Json (Content-Type: "application/json") via Post.</summary>
        /// <remarks>AuthPostData is just one value. Each SetAuthPostData replaces any previous value. It can be either a string, a byte[] or a dictionary.</remarks>
        /// <param name="dictData">A authentication-data dictionary will be converted to Json and passed to the Auth webservice via HTTP Post.</param>
        public virtual void SetAuthPostData(Dictionary<string, object> dictData)
        {
            this.AuthPostData = dictData;
        }

        /// <summary>Adds a key-value pair to the get-parameters used for Custom Auth (AuthGetParameters).</summary>
        /// <remarks>This method does uri-encoding for you.</remarks>
        /// <param name="key">Key for the value to set.</param>
        /// <param name="value">Some value relevant for Custom Authentication.</param>
        public virtual void AddAuthParameter(string key, string value)
        {
            string ampersand = string.IsNullOrEmpty(this.AuthGetParameters) ? "" : "&";
            this.AuthGetParameters = string.Format("{0}{1}{2}={3}", this.AuthGetParameters, ampersand, System.Uri.EscapeDataString(key), System.Uri.EscapeDataString(value));
        }

        /// <summary>
        /// Transform this object into string.
        /// </summary>
        /// <returns>string representation of this object.</returns>
        public override string ToString()
        {
            return string.Format("AuthenticationValues Type: {3} UserId: {0}, GetParameters: {1} Token available: {2}", this.UserId, this.AuthGetParameters, this.Token != null, this.AuthType);
        }

        /// <summary>
        /// Make a copy of the current object.
        /// </summary>
        /// <param name="copy">The object to be copied into.</param>
        /// <returns>The copied object.</returns>
        public AuthenticationValues CopyTo(AuthenticationValues copy)
        {
            copy.AuthType = this.AuthType;
            copy.AuthGetParameters = this.AuthGetParameters;
            copy.AuthPostData = this.AuthPostData;
            copy.UserId = this.UserId;
            return copy;
        }
    }

    /// <summary>
    /// ErrorCode defines the default codes associated with Photon client/server communication.
    /// </summary>
    public class ErrorCode
    {
        /// <summary>(0) is always "OK", anything else an error or specific situation.</summary>
        public const int Ok = 0;

        // server - Photon low(er) level: <= 0

        /// <summary>
        /// (-3) Operation can't be executed yet (e.g. OpJoin can't be called before being authenticated, RaiseEvent cant be used before getting into a room).
        /// </summary>
        /// <remarks>
        /// Before you call any operations on the Cloud servers, the automated client workflow must complete its authorization.
        /// In PUN, wait until State is: JoinedLobby or ConnectedToMaster
        /// </remarks>
        public const int OperationNotAllowedInCurrentState = -3;

        /// <summary>(-2) The operation you called is not implemented on the server (application) you connect to. Make sure you run the fitting applications.</summary>
        public const int InvalidOperationCode = -2;

        /// <summary>(-1) Something went wrong in the server. Try to reproduce and contact Exit Games.</summary>
        public const int InternalServerError = -1;

        // server - PhotonNetwork: 0x7FFF and down
        // logic-level error codes start with short.max

        /// <summary>(32767) Authentication failed. Possible cause: AppId is unknown to Photon (in cloud service).</summary>
        public const int InvalidAuthentication = 0x7FFF;

        /// <summary>(32766) GameId (name) already in use (can't create another). Change name.</summary>
        public const int GameIdAlreadyExists = 0x7FFF - 1;

        /// <summary>(32765) Game is full. This rarely happens when some player joined the room before your join completed.</summary>
        public const int GameFull = 0x7FFF - 2;

        /// <summary>(32764) Game is closed and can't be joined. Join another game.</summary>
        public const int GameClosed = 0x7FFF - 3;

        /// <summary>(32762) Not in use currently.</summary>
        public const int ServerFull = 0x7FFF - 5;

        /// <summary>(32761) Not in use currently.</summary>
        public const int UserBlocked = 0x7FFF - 6;

        /// <summary>(32760) Random matchmaking only succeeds if a room exists that is neither closed nor full. Repeat in a few seconds or create a new room.</summary>
        public const int NoRandomMatchFound = 0x7FFF - 7;

        /// <summary>(32758) Join can fail if the room (name) is not existing (anymore). This can happen when players leave while you join.</summary>
        public const int GameDoesNotExist = 0x7FFF - 9;

        /// <summary>(32757) Authorization on the Photon Cloud failed because the concurrent users (CCU) limit of the app's subscription is reached.</summary>
        /// <remarks>
        /// Unless you have a plan with "CCU Burst", clients might fail the authentication step during connect.
        /// Affected client are unable to call operations. Please note that players who end a game and return
        /// to the master server will disconnect and re-connect, which means that they just played and are rejected
        /// in the next minute / re-connect.
        /// This is a temporary measure. Once the CCU is below the limit, players will be able to connect an play again.
        ///
        /// OpAuthorize is part of connection workflow but only on the Photon Cloud, this error can happen.
        /// Self-hosted Photon servers with a CCU limited license won't let a client connect at all.
        /// </remarks>
        public const int MaxCcuReached = 0x7FFF - 10;

        /// <summary>(32756) Authorization on the Photon Cloud failed because the app's subscription does not allow to use a particular region's server.</summary>
        /// <remarks>
        /// Some subscription plans for the Photon Cloud are region-bound. Servers of other regions can't be used then.
        /// Check your master server address and compare it with your Photon Cloud Dashboard's info.
        /// https://cloud.photonengine.com/dashboard
        ///
        /// OpAuthorize is part of connection workflow but only on the Photon Cloud, this error can happen.
        /// Self-hosted Photon servers with a CCU limited license won't let a client connect at all.
        /// </remarks>
        public const int InvalidRegion = 0x7FFF - 11;

        /// <summary>
        /// (32755) Custom Authentication of the user failed due to setup reasons (see Cloud Dashboard) or the provided user data (like username or token). Check error message for details.
        /// </summary>
        public const int CustomAuthenticationFailed = 0x7FFF - 12;

        /// <summary>(32753) The Authentication ticket expired. Usually, this is refreshed behind the scenes. Connect (and authorize) again.</summary>
        public const int AuthenticationTicketExpired = 0x7FF1;

        /// <summary>
        /// (32743) for operations with defined limits (as in calls per second, content count or size).
        /// </summary>
        public const int OperationLimitReached = 32743; // 0x7FFF - 24,
    }
}