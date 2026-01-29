using System;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using System.Linq;

namespace Outernet.Client
{
    public class GithubURL
    {
        public string folderName;
        public string author;
        public string apiUrl;
    }

    [Serializable]
    class FileResponse
    {
        public string name;
        public string path;
        public string sha;
        public string size;
        public string url;
        public string html_url;
        public string git_url;
        public string download_url;
        public string type;
    }

    static public class GithubAPI
    {
        public static async UniTask<List<string>> GetFolderContents(string apiUrl)
        {
            var files = await RestClient.Get<List<FileResponse>>(apiUrl);

            return files
                .Select(file => file.download_url)
                .Where(url => !string.IsNullOrEmpty(url))
                .ToList();
        }


        public static GithubURL ParseFolderUrl(string rawUrl)
        {
            if (string.IsNullOrWhiteSpace(rawUrl))
                throw new ArgumentException("URL must not be empty", nameof(rawUrl));

            var uri = new Uri(rawUrl);
            // Split "/owner/repo/tree/branch/optional/path..." → ["owner","repo","tree","branch",...]
            var segments = uri.AbsolutePath
                .Trim('/')
                .Split(new[] { '/' }, StringSplitOptions.RemoveEmptyEntries);

            if (segments.Length < 4 || segments[2] != "tree")
                throw new ArgumentException(
                    "URL must be in the form https://github.com/{owner}/{repo}/tree/{branch}/…",
                    nameof(rawUrl));

            string owner = segments[0];
            string repo = segments[1];
            string branch = segments[3];

            // Recombine any path segments after the branch
            string path = segments.Length > 4
                ? string.Join("/", segments.Skip(4))
                : string.Empty;

            // Build the API URL
            string apiBase = $"https://api.github.com/repos/{owner}/{repo}/contents";
            string apiUrl = string.IsNullOrEmpty(path)
                ? $"{apiBase}?ref={branch}"
                : $"{apiBase}/{path}?ref={branch}";

            return new GithubURL
            {
                folderName = segments[1],
                author = segments[0],
                apiUrl = apiUrl
            };
        }
    }
}