using System.Net.Http;
using UnityEngine;

namespace Placeframe.Auth
{
    public abstract class AuthorizationProvider : MonoBehaviour
    {
        public abstract bool authorized { get; }
        public abstract HttpMessageHandler httpMessageHandler { get; }
    }
}
