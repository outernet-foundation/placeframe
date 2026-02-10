// ----------------------------------------------------------------------------------------------------------------------
// <summary>The Photon Chat Api enables clients to connect to a chat server and communicate with other clients.</summary>
// <remarks>ChannelWellKnownProperties contains the list of well-known channel properties.</remarks>
// <copyright company="Exit Games GmbH">Photon Chat Api - Copyright (C) 2018 Exit Games GmbH</copyright>
// ----------------------------------------------------------------------------------------------------------------------

namespace Photon.Chat
{
    /// <summary>Key codes for well known properties.</summary>
    public class ChannelWellKnownProperties
    {
        /// <summary>Maximum subscribers allowed for a channel.</summary>
        public const byte MaxSubscribers = 255;
        /// <summary>The server will publish subscriber userIDs of this channel, if true.</summary>
        public const byte PublishSubscribers = 254;
    }
}
