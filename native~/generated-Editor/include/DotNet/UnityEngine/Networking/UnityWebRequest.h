#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class String;
}
namespace DotNet::UnityEngine::Networking {
class DownloadHandler;
}
namespace DotNet::UnityEngine::Networking {
class UploadHandler;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::UnityEngine::Networking {
enum class Result;
}
namespace DotNet::UnityEngine::Networking {
class UnityWebRequest;
}
namespace DotNet::System::Collections::Generic {
template <typename T0, typename T1> class Dictionary2;
}
namespace DotNet::UnityEngine::Networking {
class UnityWebRequestAsyncOperation;
}

namespace DotNet::UnityEngine::Networking {

class UnityWebRequest {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit UnityWebRequest(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: UnityWebRequest(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_N5nF6s7__PflIcgtgQgj6DA)(void* url, void* method, void* downloadHandler, void* uploadHandler, void** reinteropException);
  public: UnityWebRequest(const ::DotNet::System::String& url, const ::DotNet::System::String& method, const ::DotNet::UnityEngine::Networking::DownloadHandler& downloadHandler, const ::DotNet::UnityEngine::Networking::UploadHandler& uploadHandler);
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint8_t (*Property_get_isDone)(void* thiz, void** reinteropException);
  public: bool isDone() const;
  private: static void* (*Property_get_error)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String error() const;
  private: static void* (*Property_get_method)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String method() const;
  private: static void (*Property_set_method)(void* thiz, void* value, void** reinteropException);
  public: void method(const ::DotNet::System::String& value) const;
  private: static void* (*Property_get_url)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String url() const;
  private: static void (*Property_set_url)(void* thiz, void* value, void** reinteropException);
  public: void url(const ::DotNet::System::String& value) const;
  private: static ::std::uint32_t (*Property_get_result)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::Networking::Result result() const;
  private: static void* (*Property_get_downloadHandler)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::Networking::DownloadHandler downloadHandler() const;
  private: static void (*Property_set_downloadHandler)(void* thiz, void* value, void** reinteropException);
  public: void downloadHandler(const ::DotNet::UnityEngine::Networking::DownloadHandler& value) const;
  private: static ::std::int64_t (*Property_get_responseCode)(void* thiz, void** reinteropException);
  public: ::std::int64_t responseCode() const;
  private: static void* (*CallGet_Y2__l4HVQ8CbSg4jpXDip9A)(void* uri, void** reinteropException);
  public: static ::DotNet::UnityEngine::Networking::UnityWebRequest Get(const ::DotNet::System::String& uri);
  private: static void (*CallAbort_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void Abort() const;
  private: static void (*CallDispose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void Dispose() const;
  private: static void (*CallSetRequestHeader_tEfBle3aSdR47_HxLakNjw)(void* thiz, void* name, void* value, void** reinteropException);
  public: void SetRequestHeader(const ::DotNet::System::String& name, const ::DotNet::System::String& value) const;
  private: static void* (*CallGetResponseHeader_wfPSjxsETIcebv8un8PGZw)(void* thiz, void* name, void** reinteropException);
  public: ::DotNet::System::String GetResponseHeader(const ::DotNet::System::String& name) const;
  private: static void* (*CallGetResponseHeaders_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Collections::Generic::Dictionary2<::DotNet::System::String, ::DotNet::System::String> GetResponseHeaders() const;
  private: static void* (*CallSendWebRequest_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::Networking::UnityWebRequestAsyncOperation SendWebRequest() const;
};

} // namespace DotNet::UnityEngine::Networking


