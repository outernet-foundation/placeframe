#include <DotNet/CesiumForUnity/NativeCoroutine.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Object.h>
#include <DotNet/System/Func2.h>
#include <DotNet/System/Collections/IEnumerator.h>



namespace DotNet::CesiumForUnity {

NativeCoroutine::NativeCoroutine(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


NativeCoroutine::NativeCoroutine(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool NativeCoroutine::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool NativeCoroutine::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& NativeCoroutine::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& NativeCoroutine::GetHandle() {
    return this->_handle;
}


void* (*NativeCoroutine::Construct_cIsazMJakk__Bsh3eD72HgQ)(void* callback, void** reinteropException) = nullptr;


NativeCoroutine::NativeCoroutine(const ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>& callback)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_cIsazMJakk__Bsh3eD72HgQ(callback.GetHandle().GetRaw(), &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


NativeCoroutine::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::NativeCoroutine::CallGetEnumerator_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Collections::IEnumerator NativeCoroutine::GetEnumerator() const {
    void* reinteropException = nullptr;
    auto result = CallGetEnumerator_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::IEnumerator(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::CesiumForUnity


