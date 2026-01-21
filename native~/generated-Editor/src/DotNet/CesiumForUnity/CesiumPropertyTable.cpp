#include <DotNet/CesiumForUnity/CesiumPropertyTable.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumPropertyTableStatus.h>
#include <DotNet/System/String.h>
#include <DotNet/CesiumForUnity/CesiumPropertyTableProperty.h>
#include <DotNet/System/Collections/Generic/Dictionary2.h>



namespace DotNet::CesiumForUnity {

CesiumPropertyTable::CesiumPropertyTable(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumPropertyTable::CesiumPropertyTable(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumPropertyTable::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumPropertyTable::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumPropertyTable::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumPropertyTable::GetHandle() {
    return this->_handle;
}


void* (*CesiumPropertyTable::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


CesiumPropertyTable::CesiumPropertyTable()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


CesiumPropertyTable::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumPropertyTable::Property_get_status)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumPropertyTableStatus CesiumPropertyTable::status() const {
    void* reinteropException = nullptr;
    auto result = Property_get_status((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPropertyTableStatus(result);
}


void (*DotNet::CesiumForUnity::CesiumPropertyTable::Property_set_status)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumPropertyTable::status(::DotNet::CesiumForUnity::CesiumPropertyTableStatus value) const {
    void* reinteropException = nullptr;
    Property_set_status((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumPropertyTable::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumPropertyTable::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumPropertyTable::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumPropertyTable::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumPropertyTable::Property_get_count)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t CesiumPropertyTable::count() const {
    void* reinteropException = nullptr;
    auto result = Property_get_count((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumPropertyTable::Property_set_count)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void CesiumPropertyTable::count(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_count((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumPropertyTable::Property_get_properties)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Collections::Generic::Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty> CesiumPropertyTable::properties() const {
    void* reinteropException = nullptr;
    auto result = Property_get_properties((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::Generic::Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumPropertyTable::Property_set_properties)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumPropertyTable::properties(const ::DotNet::System::Collections::Generic::Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>& value) const {
    void* reinteropException = nullptr;
    Property_set_properties((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumPropertyTable::CallDisposeProperties_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumPropertyTable::DisposeProperties() const {
    void* reinteropException = nullptr;
    CallDisposeProperties_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::CesiumForUnity


