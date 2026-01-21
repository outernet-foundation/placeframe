#include <DotNet/System/String.h>
#include <DotNet/System/Collections/Generic/Dictionary2.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/System/Collections/Generic/Enumerator0.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/CesiumPropertyTableProperty.h>
#include <cstdint>



namespace DotNet::System::Collections::Generic {

Dictionary2<::DotNet::System::String, ::DotNet::System::String>::Dictionary2(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Dictionary2<::DotNet::System::String, ::DotNet::System::String>::Dictionary2(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Dictionary2<::DotNet::System::String, ::DotNet::System::String>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Dictionary2<::DotNet::System::String, ::DotNet::System::String>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Dictionary2<::DotNet::System::String, ::DotNet::System::String>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Dictionary2<::DotNet::System::String, ::DotNet::System::String>::GetHandle() {
    return this->_handle;
}


Dictionary2<::DotNet::System::String, ::DotNet::System::String>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Collections::Generic::Dictionary2<::DotNet::System::String, ::DotNet::System::String>::CallGetEnumerator_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Collections::Generic::Enumerator0 Dictionary2<::DotNet::System::String, ::DotNet::System::String>::GetEnumerator() const {
    void* reinteropException = nullptr;
    auto result = CallGetEnumerator_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::Generic::Enumerator0(::DotNet::Reinterop::ObjectHandle(result));
}


Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>::Dictionary2(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>::Dictionary2(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>::GetHandle() {
    return this->_handle;
}


void* (*Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>::Construct_WGe5Irde9C7cSq7hDUfI5Q)(::std::int32_t capacity, void** reinteropException) = nullptr;


Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>::Dictionary2(::std::int32_t capacity)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_WGe5Irde9C7cSq7hDUfI5Q(capacity, &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::System::Collections::Generic::Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>::CallAdd_zclURTnfSFbfrVxWQq_LWQ)(void* thiz, void* key, void* value, void** reinteropException) = nullptr;


void Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>::Add(const ::DotNet::System::String& key, const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty& value) const {
    void* reinteropException = nullptr;
    CallAdd_zclURTnfSFbfrVxWQq_LWQ((*this).GetHandle().GetRaw(), key.GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::System::Collections::Generic


