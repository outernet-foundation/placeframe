using System;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using System.Linq;

namespace Outernet.MapRegistrationTool
{
    [Serializable]
    class NearbyAddressesRequest
    {
        public double p_latitude;
        public double p_longitude;
        public int max_distance_meters;
        public int max_results;
    }

    [Serializable]
    public class Address
    {
        public string id;
        public string address_name;
        public double address_latitude;
        public double address_longitude;
    }

    // TODO: consolidate with above once the fields have the same names
    [Serializable]
    public class AddressData
    {
        public string id;
        public string address_name;
        public string streetview;
        public float? streetview_fov;
        public float? streetview_heading;
        public float? streetview_pitch;
        public string streetview_pano_id;
        public double? streetview_latitude;
        public double? streetview_longitude;
        public double? placard_latitude;
        public double? placard_longitude;
    }

    [Serializable]
    public class AddressMedia
    {
        public string id;
        public string address_id;
        public string type;
        public string streetview_type;
        public string uri;
    }

    [Serializable]
    public class Document
    {
        public string id;
        public string title;
        public string author;
        public int? year_int;
        public string year_raw;
        public string document_key;
    }

    [Serializable]
    public class DocumentSpan
    {
        public string id;
        public string document_id;
        public int target_page;
        public int next_pages;
        public int previous_pages;
        public List<DocumentSpanPage> document_span_page;
        public List<DocumentSpanAnnotation> document_span_annotation;
        public List<DocumentSpanAddressMention> document_span_address_mention;
    }

    [Serializable]
    public class DocumentSpanPage
    {
        public string id;
        public string page_id;
        public string span_id;
        public DocumentPage document_page;
    }

    [Serializable]
    public class DocumentPage
    {
        public string id;
        public int page_num;
        public string document_id;
        public string page_image_uri;
        public string document_key;
    }

    [Serializable]
    public class DocumentSpanAnnotation
    {
        public string id;
        public string document_id;
        public string type;
        public string annotation;
        public string span_id;
        public int target_page;
        public int next_pages;
        public int previous_pages;
        public Document document;
        public DocumentSpan document_span;
    }

    [Serializable]
    public class DocumentSpanAddressMention
    {
        public string id;
        public string document_id;
        public string address_id;
        public string address_name;
        public string address_mention;
        public int target_page;
        public int next_pages;
        public int previous_pages;
        public Document document;
        public DocumentSpan document_span;
        public AddressData address;
    }

    static public class OuternetAPI
    {
        private static bool useDummyAddresses = false;
        public static bool UseDummyAddresses { get => useDummyAddresses; }

        private static string SUPABASE_BASE_URL = @"https://udbtgbqowqdqmwpaebog.supabase.co";
        private static string SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVkYnRnYnFvd3FkcW13cGFlYm9nIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTQ0MTQ1MjksImV4cCI6MjAyOTk5MDUyOX0.GKBvB3pwBEAFw1fDQkqsjKF49rrWLnGCxaom7W5lgOw";
        private static Dictionary<string, string> SUPABASE_HEADERS = new Dictionary<string, string>
        {
            { "apiKey", SUPABASE_API_KEY },
            { "Authorization", $"Bearer {SUPABASE_API_KEY}" },
            { "Accept-Profile", "v0.0.8" }
        };

        private static UniTask<T> Get<T>(string url)
        {
            return RestClient.Get<T>(url, SUPABASE_HEADERS);
        }

        public static async UniTask<List<AddressData>> GetAllAddresses()
        {
            return await Get<List<AddressData>>($"{SUPABASE_BASE_URL}/rest/v1/address?select=*");
        }

        public static async UniTask<AddressData> GetAddressData(string addressID, params string[] columns) //TODO : Support columns
        {
            var addressDatas = await Get<List<AddressData>>($"{SUPABASE_BASE_URL}/rest/v1/address?select=*&id=eq.{addressID}");

            return addressDatas.FirstOrDefault();
        }

        public static async UniTask<List<DocumentSpanAddressMention>> GetDocumentSpanAddressMentions(string addressID)
        {
            var mentions = await Get<List<DocumentSpanAddressMention>>($"{SUPABASE_BASE_URL}/rest/v1/document_span_address_mention?address_id=eq.{addressID}&select=*,document(*),document_span(*,document_span_page(*,document_page(*)),document_span_annotation(*))");
            return mentions.Take(5).ToList();
        }

        public static async UniTask<List<DocumentSpanAddressMention>> GetDocumentSpanAddressMention(string id)
        {
            return await Get<List<DocumentSpanAddressMention>>($"{SUPABASE_BASE_URL}/rest/v1/document_span_address_mention?id=eq.{id}&select=*,document(*),document_span(*,document_span_page(*,document_page(*)),document_span_annotation(*))");
        }

        public static async UniTask<List<AddressMedia>> GetAddressMedia(string addressID)
        {
            return await Get<List<AddressMedia>>($"{SUPABASE_BASE_URL}/rest/v1/address_media?select=*&address_id=eq.{addressID}");
        }

        public static async UniTask<AddressData> GetAddressDataByName(string addressName, params string[] columns) //TODO : Support columns
        {
            try
            {
                var addressDatas = await Get<List<AddressData>>($"{SUPABASE_BASE_URL}/rest/v1/address?select=*&address_name=eq.{addressName}");

                return addressDatas.FirstOrDefault();
            }
            catch (Exception e)
            {
                Log.Error(e, "Failed to fetch address");
                return null;
            }
        }

        public static async UniTask<DocumentSpanAnnotation> GetAnnotation(string id)
        {
            try
            {
                var annotations = await Get<List<DocumentSpanAnnotation>>($"{SUPABASE_BASE_URL}/rest/v1/document_span_annotation?id=eq.{id}&select=*,document(*),document_span(*,document_span_page(*,document_page(*)),document_span_address_mention(*))");

                return annotations.FirstOrDefault();
            }
            catch (Exception e)
            {
                Log.Error(e, "Failed to fetch annotation");
                return null;
            }
        }
    }
}