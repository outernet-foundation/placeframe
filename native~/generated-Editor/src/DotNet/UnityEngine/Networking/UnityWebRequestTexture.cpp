#include <DotNet/UnityEngine/Networking/UnityWebRequestTexture.h>
#include <DotNet/UnityEngine/Networking/UnityWebRequest.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/String.h>



namespace DotNet::UnityEngine::Networking {

void* (*DotNet::UnityEngine::Networking::UnityWebRequestTexture::CallGetTexture_Y2__l4HVQ8CbSg4jpXDip9A)(void* uri, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Networking::UnityWebRequest UnityWebRequestTexture::GetTexture(const ::DotNet::System::String& uri) {
    void* reinteropException = nullptr;
    auto result = CallGetTexture_Y2__l4HVQ8CbSg4jpXDip9A(uri.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Networking::UnityWebRequest(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::UnityEngine::Networking


