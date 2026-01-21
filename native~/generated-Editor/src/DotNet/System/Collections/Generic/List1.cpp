#include <DotNet/CesiumForUnity/QuickAddItem.h>
#include <DotNet/System/Collections/Generic/List1.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Object.h>
#include <DotNet/System/String.h>
#include <cstdint>
#include <DotNet/System/Array1.h>
#include <DotNet/CesiumForUnity/GoogleMapTilesLayerType.h>
#include <DotNet/CesiumForUnity/HeaderEntry.h>
#include <DotNet/CesiumForUnity/CesiumCreditComponent.h>
#include <DotNet/CesiumForUnity/CesiumCredit.h>
#include <DotNet/UnityEngine/Texture2D.h>
#include <DotNet/Unity/Mathematics/double2.h>
#include <DotNet/CesiumForUnity/CesiumCartographicPolygon.h>
#include <DotNet/UnityEngine/Camera.h>



namespace DotNet::System::Collections::Generic {

List1<::DotNet::CesiumForUnity::QuickAddItem>::List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


List1<::DotNet::CesiumForUnity::QuickAddItem>::List1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool List1<::DotNet::CesiumForUnity::QuickAddItem>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool List1<::DotNet::CesiumForUnity::QuickAddItem>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& List1<::DotNet::CesiumForUnity::QuickAddItem>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& List1<::DotNet::CesiumForUnity::QuickAddItem>::GetHandle() {
    return this->_handle;
}


void* (*List1<::DotNet::CesiumForUnity::QuickAddItem>::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


List1<::DotNet::CesiumForUnity::QuickAddItem>::List1()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


List1<::DotNet::CesiumForUnity::QuickAddItem>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::QuickAddItem>::CallAdd_nq8TJwFX_ptyb2rCV3CGsw)(void* thiz, void* item, void** reinteropException) = nullptr;


void List1<::DotNet::CesiumForUnity::QuickAddItem>::Add(const ::DotNet::CesiumForUnity::QuickAddItem& item) const {
    void* reinteropException = nullptr;
    CallAdd_nq8TJwFX_ptyb2rCV3CGsw((*this).GetHandle().GetRaw(), item.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


List1<::DotNet::System::String>::List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


List1<::DotNet::System::String>::List1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool List1<::DotNet::System::String>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool List1<::DotNet::System::String>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& List1<::DotNet::System::String>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& List1<::DotNet::System::String>::GetHandle() {
    return this->_handle;
}


void* (*List1<::DotNet::System::String>::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


List1<::DotNet::System::String>::List1()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


List1<::DotNet::System::String>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::System::Collections::Generic::List1<::DotNet::System::String>::Property_get_Count)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t List1<::DotNet::System::String>::Count() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Count((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::System::Collections::Generic::List1<::DotNet::System::String>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::System::String List1<::DotNet::System::String>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::System::Collections::Generic::List1<::DotNet::System::String>::CallClear_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void List1<::DotNet::System::String>::Clear() const {
    void* reinteropException = nullptr;
    CallClear_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::System::Collections::Generic::List1<::DotNet::System::String>::CallAdd_LRSjiXmrvb5pgfbcZ_Nv7w)(void* thiz, void* item, void** reinteropException) = nullptr;


void List1<::DotNet::System::String>::Add(const ::DotNet::System::String& item) const {
    void* reinteropException = nullptr;
    CallAdd_LRSjiXmrvb5pgfbcZ_Nv7w((*this).GetHandle().GetRaw(), item.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::System::Collections::Generic::List1<::DotNet::System::String>::CallToArray_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Array1<::DotNet::System::String> List1<::DotNet::System::String>::ToArray() const {
    void* reinteropException = nullptr;
    auto result = CallToArray_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::System::String>(::DotNet::Reinterop::ObjectHandle(result));
}


List1<::std::int32_t>::List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


List1<::std::int32_t>::List1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool List1<::std::int32_t>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool List1<::std::int32_t>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& List1<::std::int32_t>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& List1<::std::int32_t>::GetHandle() {
    return this->_handle;
}


void* (*List1<::std::int32_t>::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


List1<::std::int32_t>::List1()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


List1<::std::int32_t>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::System::Collections::Generic::List1<::std::int32_t>::Property_get_Count)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t List1<::std::int32_t>::Count() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Count((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int32_t (*DotNet::System::Collections::Generic::List1<::std::int32_t>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::std::int32_t List1<::std::int32_t>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::List1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::GetHandle() {
    return this->_handle;
}


void* (*List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::List1()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::Property_get_Count)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::Count() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Count((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::uint32_t (*DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::GoogleMapTilesLayerType List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::GoogleMapTilesLayerType(result);
}


List1<::DotNet::CesiumForUnity::HeaderEntry>::List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


List1<::DotNet::CesiumForUnity::HeaderEntry>::List1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool List1<::DotNet::CesiumForUnity::HeaderEntry>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool List1<::DotNet::CesiumForUnity::HeaderEntry>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& List1<::DotNet::CesiumForUnity::HeaderEntry>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& List1<::DotNet::CesiumForUnity::HeaderEntry>::GetHandle() {
    return this->_handle;
}


List1<::DotNet::CesiumForUnity::HeaderEntry>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::HeaderEntry>::Property_get_Count)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t List1<::DotNet::CesiumForUnity::HeaderEntry>::Count() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Count((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::HeaderEntry>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::HeaderEntry List1<::DotNet::CesiumForUnity::HeaderEntry>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::HeaderEntry(::DotNet::Reinterop::ObjectHandle(result));
}


List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::List1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::GetHandle() {
    return this->_handle;
}


void* (*List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::List1()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::Property_get_Count)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::Count() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Count((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::CallAdd_VqNpQ4Sqmxp7DzXSAQsehQ)(void* thiz, void* item, void** reinteropException) = nullptr;


void List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::Add(const ::DotNet::CesiumForUnity::CesiumCreditComponent& item) const {
    void* reinteropException = nullptr;
    CallAdd_VqNpQ4Sqmxp7DzXSAQsehQ((*this).GetHandle().GetRaw(), item.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


List1<::DotNet::CesiumForUnity::CesiumCredit>::List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


List1<::DotNet::CesiumForUnity::CesiumCredit>::List1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool List1<::DotNet::CesiumForUnity::CesiumCredit>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool List1<::DotNet::CesiumForUnity::CesiumCredit>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& List1<::DotNet::CesiumForUnity::CesiumCredit>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& List1<::DotNet::CesiumForUnity::CesiumCredit>::GetHandle() {
    return this->_handle;
}


List1<::DotNet::CesiumForUnity::CesiumCredit>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCredit>::CallAdd_DnUt__NGf__FxtU__keZH5Geg)(void* thiz, void* item, void** reinteropException) = nullptr;


void List1<::DotNet::CesiumForUnity::CesiumCredit>::Add(const ::DotNet::CesiumForUnity::CesiumCredit& item) const {
    void* reinteropException = nullptr;
    CallAdd_DnUt__NGf__FxtU__keZH5Geg((*this).GetHandle().GetRaw(), item.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCredit>::CallClear_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void List1<::DotNet::CesiumForUnity::CesiumCredit>::Clear() const {
    void* reinteropException = nullptr;
    CallClear_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


List1<::DotNet::UnityEngine::Texture2D>::List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


List1<::DotNet::UnityEngine::Texture2D>::List1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool List1<::DotNet::UnityEngine::Texture2D>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool List1<::DotNet::UnityEngine::Texture2D>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& List1<::DotNet::UnityEngine::Texture2D>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& List1<::DotNet::UnityEngine::Texture2D>::GetHandle() {
    return this->_handle;
}


List1<::DotNet::UnityEngine::Texture2D>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::System::Collections::Generic::List1<::DotNet::UnityEngine::Texture2D>::Property_get_Count)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t List1<::DotNet::UnityEngine::Texture2D>::Count() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Count((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


List1<::DotNet::Unity::Mathematics::double2>::List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


List1<::DotNet::Unity::Mathematics::double2>::List1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool List1<::DotNet::Unity::Mathematics::double2>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool List1<::DotNet::Unity::Mathematics::double2>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& List1<::DotNet::Unity::Mathematics::double2>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& List1<::DotNet::Unity::Mathematics::double2>::GetHandle() {
    return this->_handle;
}


List1<::DotNet::Unity::Mathematics::double2>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::System::Collections::Generic::List1<::DotNet::Unity::Mathematics::double2>::Property_get_Count)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t List1<::DotNet::Unity::Mathematics::double2>::Count() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Count((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::System::Collections::Generic::List1<::DotNet::Unity::Mathematics::double2>::Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::double2* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::double2 List1<::DotNet::Unity::Mathematics::double2>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double2 result;
    Property_get_Item((*this).GetHandle().GetRaw(), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


List1<::DotNet::CesiumForUnity::CesiumCartographicPolygon>::List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


List1<::DotNet::CesiumForUnity::CesiumCartographicPolygon>::List1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool List1<::DotNet::CesiumForUnity::CesiumCartographicPolygon>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool List1<::DotNet::CesiumForUnity::CesiumCartographicPolygon>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& List1<::DotNet::CesiumForUnity::CesiumCartographicPolygon>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& List1<::DotNet::CesiumForUnity::CesiumCartographicPolygon>::GetHandle() {
    return this->_handle;
}


List1<::DotNet::CesiumForUnity::CesiumCartographicPolygon>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCartographicPolygon>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumCartographicPolygon List1<::DotNet::CesiumForUnity::CesiumCartographicPolygon>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumCartographicPolygon(::DotNet::Reinterop::ObjectHandle(result));
}


::std::int32_t (*DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCartographicPolygon>::Property_get_Count)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t List1<::DotNet::CesiumForUnity::CesiumCartographicPolygon>::Count() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Count((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


List1<::DotNet::UnityEngine::Camera>::List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


List1<::DotNet::UnityEngine::Camera>::List1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool List1<::DotNet::UnityEngine::Camera>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool List1<::DotNet::UnityEngine::Camera>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& List1<::DotNet::UnityEngine::Camera>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& List1<::DotNet::UnityEngine::Camera>::GetHandle() {
    return this->_handle;
}


List1<::DotNet::UnityEngine::Camera>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::System::Collections::Generic::List1<::DotNet::UnityEngine::Camera>::Property_get_Count)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t List1<::DotNet::UnityEngine::Camera>::Count() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Count((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::System::Collections::Generic::List1<::DotNet::UnityEngine::Camera>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Camera List1<::DotNet::UnityEngine::Camera>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Camera(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::System::Collections::Generic


