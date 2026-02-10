// -----------------------------------------------------------------------
// <copyright file="ChatAppSettings.cs" company="Exit Games GmbH">
//   Chat API for Photon - Copyright (C) 2018 Exit Games GmbH
// </copyright>
// <summary>Settings for Photon Chat application and the server to connect to.</summary>
// <author>developer@photonengine.com</author>
// ----------------------------------------------------------------------------

#if UNITY_2017_4_OR_NEWER
#define SUPPORTED_UNITY
#endif


namespace Photon.Chat
{
    using System;
    using Photon.Client;
    #if SUPPORTED_UNITY
    using UnityEngine.Serialization;
    #endif

    /// <summary>
    /// Settings for Photon application(s) and the server to connect to.
    /// </summary>
    /// <remarks>
    /// This is Serializable for Unity, so it can be included in ScriptableObject instances.
    /// </remarks>
    #if SUPPORTED_UNITY
    [Serializable]
    #endif
    public class ChatAppSettings
    {
        /// <summary>AppId for the Chat Api.</summary>
        public string AppIdChat;

        /// <summary>The AppVersion can be used to identify builds and will split the AppId distinct "Virtual AppIds" (important for the users to find each other).</summary>
        public string AppVersion;

        /// <summary>Can be set to any of the Photon Cloud's region names to directly connect to that region.</summary>
        public string FixedRegion;

        /// <summary>The address (hostname or IP) of the server to connect to.</summary>
        public string Server;

        /// <summary>If not null, this sets the port of the first Photon server to connect to (that will "forward" the client as needed).</summary>
        public ushort Port;

        /// <summary>The address (hostname or IP and port) of the proxy server.</summary>
        public string ProxyServer;

        /// <summary>The network level protocol to use.</summary>
        public ConnectionProtocol Protocol = ConnectionProtocol.Udp;

        /// <summary>Enables a fallback to another protocol in case a connect to the Name Server fails.</summary>
        /// <remarks>See: LoadBalancingClient.EnableProtocolFallback.</remarks>
        public bool EnableProtocolFallback = true;

        /// <summary>Log level for the network lib. Useful to get info about low level connection and state.</summary>
        public LogLevel NetworkLogging = LogLevel.Error;

        /// <summary>Log level for the ChatClient and callbacks. Useful to get info about the client state, servers it uses and operations called.</summary>
        public LogLevel ClientLogging = LogLevel.Warning;

        /// <summary>If true, the default nameserver address for the Photon Cloud should be used.</summary>
        public bool IsDefaultNameServer { get { return string.IsNullOrEmpty(this.Server); } }

        /// <summary>If true, the default ports for a protocol will be used.</summary>
        public bool IsDefaultPort
        {
            get { return this.Port <= 0; }
        }
        
        /// <summary>Creates an ChatAppSettings instance with default values.</summary>
        public ChatAppSettings()
        {
        }

        /// <summary>
        /// Initializes the ChatAppSettings with default values or the provided original.
        /// </summary>
        /// <param name="original">If non-null, all values are copied from the original.</param>
        public ChatAppSettings(ChatAppSettings original)
        {
            if (original != null)
            {
                original.CopyTo(this);
            }
        }
        
        /// <summary>Copies values of this instance to the target.</summary>
        /// <param name="target">Target instance.</param>
        /// <returns>The target.</returns>
        public ChatAppSettings CopyTo(ChatAppSettings target)
        {
            //target.AppIdRealtime = this.AppIdRealtime;
            //target.AppIdFusion = this.AppIdFusion;
            //target.AppIdQuantum = this.AppIdQuantum;
            target.AppIdChat = this.AppIdChat;
            //target.AppIdVoice = this.AppIdVoice;
            target.AppVersion = this.AppVersion;
            //target.UseNameServer = this.UseNameServer;
            target.FixedRegion = this.FixedRegion;
            //target.BestRegionSummaryFromStorage = this.BestRegionSummaryFromStorage;
            target.Server = this.Server;
            target.Port = this.Port;
            target.ProxyServer = this.ProxyServer;
            target.Protocol = this.Protocol;
            //target.AuthMode = this.AuthMode;
            //target.EnableLobbyStatistics = this.EnableLobbyStatistics;
            target.ClientLogging = this.ClientLogging;
            target.NetworkLogging = this.NetworkLogging;
            target.EnableProtocolFallback = this.EnableProtocolFallback;
            return target;
        }
    }
}