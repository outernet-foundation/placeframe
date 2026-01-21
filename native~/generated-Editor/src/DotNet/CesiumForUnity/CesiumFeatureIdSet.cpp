#include <DotNet/CesiumForUnity/CesiumFeatureIdSet.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>
#include <DotNet/System/Object.h>
#include <DotNet/System/String.h>



namespace DotNet::CesiumForUnity {

CesiumFeatureIdSet::CesiumFeatureIdSet(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumFeatureIdSet::CesiumFeatureIdSet(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumFeatureIdSet::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumFeatureIdSet::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumFeatureIdSet::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumFeatureIdSet::GetHandle() {
    return this->_handle;
}


void* (*CesiumFeatureIdSet::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


CesiumFeatureIdSet::CesiumFeatureIdSet()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


void* (*CesiumFeatureIdSet::Construct_AdNLRR1TzhjQ9htOxA80Nw)(::std::int64_t featureCount, void** reinteropException) = nullptr;


CesiumFeatureIdSet::CesiumFeatureIdSet(::std::int64_t featureCount)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_AdNLRR1TzhjQ9htOxA80Nw(featureCount, &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


CesiumFeatureIdSet::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_get_featureCount)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t CesiumFeatureIdSet::featureCount() const {
    void* reinteropException = nullptr;
    auto result = Property_get_featureCount((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_set_featureCount)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void CesiumFeatureIdSet::featureCount(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_featureCount((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_get_label)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumFeatureIdSet::label() const {
    void* reinteropException = nullptr;
    auto result = Property_get_label((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_set_label)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumFeatureIdSet::label(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_label((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_get_nullFeatureId)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t CesiumFeatureIdSet::nullFeatureId() const {
    void* reinteropException = nullptr;
    auto result = Property_get_nullFeatureId((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_set_nullFeatureId)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void CesiumFeatureIdSet::nullFeatureId(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_nullFeatureId((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_get_propertyTableIndex)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t CesiumFeatureIdSet::propertyTableIndex() const {
    void* reinteropException = nullptr;
    auto result = Property_get_propertyTableIndex((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_set_propertyTableIndex)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void CesiumFeatureIdSet::propertyTableIndex(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_propertyTableIndex((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumFeatureIdSet::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumFeatureIdSet::Dispose() const {
    void* reinteropException = nullptr;
    CallDispose_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::CesiumForUnity


