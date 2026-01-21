#include <DotNet/UnityEngine/Networking/UploadHandlerRaw.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>
#include <DotNet/System/Array1.h>
#include <DotNet/Unity/Collections/NativeArray1.h>
#include <DotNet/UnityEngine/Networking/UploadHandler.h>
#include <DotNet/System/Object.h>



namespace DotNet::UnityEngine::Networking {

UploadHandlerRaw::UploadHandlerRaw(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


UploadHandlerRaw::UploadHandlerRaw(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool UploadHandlerRaw::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool UploadHandlerRaw::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& UploadHandlerRaw::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& UploadHandlerRaw::GetHandle() {
    return this->_handle;
}


void* (*UploadHandlerRaw::Construct_Wn8TTeG3Q36ufSfvO3m1sg)(void* data, void** reinteropException) = nullptr;


UploadHandlerRaw::UploadHandlerRaw(const ::DotNet::System::Array1<::std::uint8_t>& data)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_Wn8TTeG3Q36ufSfvO3m1sg(data.GetHandle().GetRaw(), &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


void* (*UploadHandlerRaw::Construct_j9VUe_obWzqxHm0yKnVCmg)(void* data, ::std::uint8_t transferOwnership, void** reinteropException) = nullptr;


UploadHandlerRaw::UploadHandlerRaw(const ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>& data, bool transferOwnership)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_j9VUe_obWzqxHm0yKnVCmg(data.GetHandle().GetRaw(), transferOwnership ? 1 : 0, &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


UploadHandlerRaw::operator ::DotNet::UnityEngine::Networking::UploadHandler() const {
    return ::DotNet::UnityEngine::Networking::UploadHandler(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


UploadHandlerRaw::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


} // namespace DotNet::UnityEngine::Networking


