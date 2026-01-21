#include <cstdint>
#include <DotNet/System/Array1.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Array.h>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/Cesium3DTileset.h>
#include <DotNet/CesiumForUnity/CesiumRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumIonRasterOverlay.h>
#include <DotNet/UnityEngine/Mesh.h>
#include <DotNet/UnityEngine/Vector3.h>
#include <DotNet/System/String.h>
#include <DotNet/CesiumForUnity/CesiumFeature.h>
#include <DotNet/UnityEngine/GameObject.h>
#include <DotNet/UnityEngine/Rendering/VertexAttributeDescriptor.h>
#include <DotNet/CesiumForUnity/CesiumGlobeAnchor.h>
#include <DotNet/CesiumForUnity/CesiumTileExcluder.h>
#include <DotNet/CesiumForUnity/CesiumMetadataValue.h>
#include <DotNet/CesiumForUnity/CesiumFeatureIdSet.h>
#include <DotNet/CesiumForUnity/CesiumPropertyTable.h>
#include <DotNet/Unity/Mathematics/float2.h>
#include <DotNet/Unity/Mathematics/float3.h>
#include <DotNet/Unity/Mathematics/float4.h>
#include <DotNet/Unity/Mathematics/float2x2.h>
#include <DotNet/Unity/Mathematics/float3x3.h>
#include <DotNet/Unity/Mathematics/float4x4.h>
#include <DotNet/Unity/Mathematics/double3.h>



namespace DotNet::System {

Array1<::std::uint8_t>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::std::uint8_t>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::std::uint8_t>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::std::uint8_t>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::std::uint8_t>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::std::uint8_t>::GetHandle() {
    return this->_handle;
}


Array1<::std::uint8_t>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::std::uint8_t>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::System::Array1<::std::uint8_t>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::std::uint8_t>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::std::uint8_t>::Construct_Size)(std::int32_t) = nullptr;


Array1<::std::uint8_t>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::std::uint8_t>::SetItem)(void* thiz, std::int32_t, ::std::uint8_t value) = nullptr;


void Array1<::std::uint8_t>::Item(std::int32_t index, ::std::uint8_t value) {
  SetItem((*this).GetHandle().GetRaw(), index, value);
}


Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::Cesium3DTileset Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::Cesium3DTileset(::DotNet::Reinterop::ObjectHandle(result));
}


::std::int32_t (*DotNet::System::Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::SetItem)(void* thiz, std::int32_t, void* value) = nullptr;


void Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::Item(std::int32_t index, const ::DotNet::CesiumForUnity::Cesium3DTileset& value) {
  SetItem((*this).GetHandle().GetRaw(), index, value.GetHandle().GetRaw());
}


Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumRasterOverlay Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumRasterOverlay(::DotNet::Reinterop::ObjectHandle(result));
}


::std::int32_t (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::SetItem)(void* thiz, std::int32_t, void* value) = nullptr;


void Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumRasterOverlay& value) {
  SetItem((*this).GetHandle().GetRaw(), index, value.GetHandle().GetRaw());
}


Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIonRasterOverlay Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumIonRasterOverlay(::DotNet::Reinterop::ObjectHandle(result));
}


::std::int32_t (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::SetItem)(void* thiz, std::int32_t, void* value) = nullptr;


void Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumIonRasterOverlay& value) {
  SetItem((*this).GetHandle().GetRaw(), index, value.GetHandle().GetRaw());
}


Array1<::DotNet::UnityEngine::Mesh>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::UnityEngine::Mesh>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::UnityEngine::Mesh>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::UnityEngine::Mesh>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::UnityEngine::Mesh>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::UnityEngine::Mesh>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::UnityEngine::Mesh>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::UnityEngine::Mesh>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Array1<::DotNet::UnityEngine::Mesh>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Mesh Array1<::DotNet::UnityEngine::Mesh>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Mesh(::DotNet::Reinterop::ObjectHandle(result));
}


::std::int32_t (*DotNet::System::Array1<::DotNet::UnityEngine::Mesh>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::UnityEngine::Mesh>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::UnityEngine::Mesh>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::UnityEngine::Mesh>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::UnityEngine::Mesh>::SetItem)(void* thiz, std::int32_t, void* value) = nullptr;


void Array1<::DotNet::UnityEngine::Mesh>::Item(std::int32_t index, const ::DotNet::UnityEngine::Mesh& value) {
  SetItem((*this).GetHandle().GetRaw(), index, value.GetHandle().GetRaw());
}


Array1<::DotNet::UnityEngine::Vector3>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::UnityEngine::Vector3>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::UnityEngine::Vector3>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::UnityEngine::Vector3>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::UnityEngine::Vector3>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::UnityEngine::Vector3>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::UnityEngine::Vector3>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::UnityEngine::Vector3>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::System::Array1<::DotNet::UnityEngine::Vector3>::Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Vector3 Array1<::DotNet::UnityEngine::Vector3>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Vector3 result;
    Property_get_Item((*this).GetHandle().GetRaw(), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int32_t (*DotNet::System::Array1<::DotNet::UnityEngine::Vector3>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::UnityEngine::Vector3>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::UnityEngine::Vector3>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::UnityEngine::Vector3>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::UnityEngine::Vector3>::SetItem)(void* thiz, std::int32_t, const ::DotNet::UnityEngine::Vector3* value) = nullptr;


void Array1<::DotNet::UnityEngine::Vector3>::Item(std::int32_t index, const ::DotNet::UnityEngine::Vector3& value) {
  SetItem((*this).GetHandle().GetRaw(), index, &value);
}


Array1<::DotNet::System::String>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::System::String>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::System::String>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::System::String>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::System::String>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::System::String>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::System::String>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::System::String>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Array1<::DotNet::System::String>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::System::String Array1<::DotNet::System::String>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


::std::int32_t (*DotNet::System::Array1<::DotNet::System::String>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::System::String>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::System::String>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::System::String>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::System::String>::SetItem)(void* thiz, std::int32_t, void* value) = nullptr;


void Array1<::DotNet::System::String>::Item(std::int32_t index, const ::DotNet::System::String& value) {
  SetItem((*this).GetHandle().GetRaw(), index, value.GetHandle().GetRaw());
}


Array1<::DotNet::CesiumForUnity::CesiumFeature>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::CesiumForUnity::CesiumFeature>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::CesiumForUnity::CesiumFeature>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::CesiumForUnity::CesiumFeature>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumFeature>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumFeature>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::CesiumForUnity::CesiumFeature>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::CesiumForUnity::CesiumFeature>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeature>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumFeature Array1<::DotNet::CesiumForUnity::CesiumFeature>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumFeature(::DotNet::Reinterop::ObjectHandle(result));
}


::std::int32_t (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeature>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::CesiumForUnity::CesiumFeature>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::CesiumForUnity::CesiumFeature>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::CesiumForUnity::CesiumFeature>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::CesiumForUnity::CesiumFeature>::SetItem)(void* thiz, std::int32_t, void* value) = nullptr;


void Array1<::DotNet::CesiumForUnity::CesiumFeature>::Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumFeature& value) {
  SetItem((*this).GetHandle().GetRaw(), index, value.GetHandle().GetRaw());
}


Array1<::DotNet::UnityEngine::GameObject>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::UnityEngine::GameObject>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::UnityEngine::GameObject>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::UnityEngine::GameObject>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::UnityEngine::GameObject>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::UnityEngine::GameObject>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::UnityEngine::GameObject>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::UnityEngine::GameObject>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Array1<::DotNet::UnityEngine::GameObject>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::UnityEngine::GameObject Array1<::DotNet::UnityEngine::GameObject>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::GameObject(::DotNet::Reinterop::ObjectHandle(result));
}


::std::int32_t (*DotNet::System::Array1<::DotNet::UnityEngine::GameObject>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::UnityEngine::GameObject>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::UnityEngine::GameObject>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::UnityEngine::GameObject>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::UnityEngine::GameObject>::SetItem)(void* thiz, std::int32_t, void* value) = nullptr;


void Array1<::DotNet::UnityEngine::GameObject>::Item(std::int32_t index, const ::DotNet::UnityEngine::GameObject& value) {
  SetItem((*this).GetHandle().GetRaw(), index, value.GetHandle().GetRaw());
}


Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::System::Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor result;
    Property_get_Item((*this).GetHandle().GetRaw(), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int32_t (*DotNet::System::Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::SetItem)(void* thiz, std::int32_t, const ::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor* value) = nullptr;


void Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::Item(std::int32_t index, const ::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor& value) {
  SetItem((*this).GetHandle().GetRaw(), index, &value);
}


Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumGlobeAnchor Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumGlobeAnchor(::DotNet::Reinterop::ObjectHandle(result));
}


::std::int32_t (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::SetItem)(void* thiz, std::int32_t, void* value) = nullptr;


void Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumGlobeAnchor& value) {
  SetItem((*this).GetHandle().GetRaw(), index, value.GetHandle().GetRaw());
}


Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumTileExcluder Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumTileExcluder(::DotNet::Reinterop::ObjectHandle(result));
}


::std::int32_t (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::SetItem)(void* thiz, std::int32_t, void* value) = nullptr;


void Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumTileExcluder& value) {
  SetItem((*this).GetHandle().GetRaw(), index, value.GetHandle().GetRaw());
}


Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumMetadataValue Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(result));
}


::std::int32_t (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::SetItem)(void* thiz, std::int32_t, void* value) = nullptr;


void Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumMetadataValue& value) {
  SetItem((*this).GetHandle().GetRaw(), index, value.GetHandle().GetRaw());
}


Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumFeatureIdSet Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumFeatureIdSet(::DotNet::Reinterop::ObjectHandle(result));
}


::std::int32_t (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::SetItem)(void* thiz, std::int32_t, void* value) = nullptr;


void Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumFeatureIdSet& value) {
  SetItem((*this).GetHandle().GetRaw(), index, value.GetHandle().GetRaw());
}


Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumPropertyTable Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPropertyTable(::DotNet::Reinterop::ObjectHandle(result));
}


::std::int32_t (*DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::SetItem)(void* thiz, std::int32_t, void* value) = nullptr;


void Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumPropertyTable& value) {
  SetItem((*this).GetHandle().GetRaw(), index, value.GetHandle().GetRaw());
}


Array1<bool>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<bool>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<bool>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<bool>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<bool>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<bool>::GetHandle() {
    return this->_handle;
}


Array1<bool>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<bool>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint8_t (*DotNet::System::Array1<bool>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


bool Array1<bool>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::System::Array1<bool>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<bool>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<bool>::Construct_Size)(std::int32_t) = nullptr;


Array1<bool>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<bool>::SetItem)(void* thiz, std::int32_t, ::std::uint8_t value) = nullptr;


void Array1<bool>::Item(std::int32_t index, bool value) {
  SetItem((*this).GetHandle().GetRaw(), index, value ? 1 : 0);
}


Array1<::std::uint16_t>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::std::uint16_t>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::std::uint16_t>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::std::uint16_t>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::std::uint16_t>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::std::uint16_t>::GetHandle() {
    return this->_handle;
}


Array1<::std::uint16_t>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::std::uint16_t>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint16_t (*DotNet::System::Array1<::std::uint16_t>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::std::uint16_t Array1<::std::uint16_t>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int32_t (*DotNet::System::Array1<::std::uint16_t>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::std::uint16_t>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::std::uint16_t>::Construct_Size)(std::int32_t) = nullptr;


Array1<::std::uint16_t>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::std::uint16_t>::SetItem)(void* thiz, std::int32_t, ::std::uint16_t value) = nullptr;


void Array1<::std::uint16_t>::Item(std::int32_t index, ::std::uint16_t value) {
  SetItem((*this).GetHandle().GetRaw(), index, value);
}


Array1<::std::int32_t>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::std::int32_t>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::std::int32_t>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::std::int32_t>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::std::int32_t>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::std::int32_t>::GetHandle() {
    return this->_handle;
}


Array1<::std::int32_t>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::std::int32_t>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::System::Array1<::std::int32_t>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::std::int32_t Array1<::std::int32_t>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int32_t (*DotNet::System::Array1<::std::int32_t>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::std::int32_t>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::std::int32_t>::Construct_Size)(std::int32_t) = nullptr;


Array1<::std::int32_t>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::std::int32_t>::SetItem)(void* thiz, std::int32_t, ::std::int32_t value) = nullptr;


void Array1<::std::int32_t>::Item(std::int32_t index, ::std::int32_t value) {
  SetItem((*this).GetHandle().GetRaw(), index, value);
}


Array1<double>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<double>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<double>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<double>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<double>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<double>::GetHandle() {
    return this->_handle;
}


Array1<double>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<double>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


double (*DotNet::System::Array1<double>::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


double Array1<double>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int32_t (*DotNet::System::Array1<double>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<double>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<double>::Construct_Size)(std::int32_t) = nullptr;


Array1<double>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<double>::SetItem)(void* thiz, std::int32_t, double value) = nullptr;


void Array1<double>::Item(std::int32_t index, double value) {
  SetItem((*this).GetHandle().GetRaw(), index, value);
}


Array1<::DotNet::Unity::Mathematics::float2>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::Unity::Mathematics::float2>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::Unity::Mathematics::float2>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::Unity::Mathematics::float2>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::Unity::Mathematics::float2>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::Unity::Mathematics::float2>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::Unity::Mathematics::float2>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::Unity::Mathematics::float2>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::System::Array1<::DotNet::Unity::Mathematics::float2>::Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float2* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::float2 Array1<::DotNet::Unity::Mathematics::float2>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::float2 result;
    Property_get_Item((*this).GetHandle().GetRaw(), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int32_t (*DotNet::System::Array1<::DotNet::Unity::Mathematics::float2>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::Unity::Mathematics::float2>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::Unity::Mathematics::float2>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::Unity::Mathematics::float2>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::Unity::Mathematics::float2>::SetItem)(void* thiz, std::int32_t, const ::DotNet::Unity::Mathematics::float2* value) = nullptr;


void Array1<::DotNet::Unity::Mathematics::float2>::Item(std::int32_t index, const ::DotNet::Unity::Mathematics::float2& value) {
  SetItem((*this).GetHandle().GetRaw(), index, &value);
}


Array1<::DotNet::Unity::Mathematics::float3>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::Unity::Mathematics::float3>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::Unity::Mathematics::float3>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::Unity::Mathematics::float3>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::Unity::Mathematics::float3>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::Unity::Mathematics::float3>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::Unity::Mathematics::float3>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::Unity::Mathematics::float3>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::System::Array1<::DotNet::Unity::Mathematics::float3>::Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::float3 Array1<::DotNet::Unity::Mathematics::float3>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::float3 result;
    Property_get_Item((*this).GetHandle().GetRaw(), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int32_t (*DotNet::System::Array1<::DotNet::Unity::Mathematics::float3>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::Unity::Mathematics::float3>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::Unity::Mathematics::float3>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::Unity::Mathematics::float3>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::Unity::Mathematics::float3>::SetItem)(void* thiz, std::int32_t, const ::DotNet::Unity::Mathematics::float3* value) = nullptr;


void Array1<::DotNet::Unity::Mathematics::float3>::Item(std::int32_t index, const ::DotNet::Unity::Mathematics::float3& value) {
  SetItem((*this).GetHandle().GetRaw(), index, &value);
}


Array1<::DotNet::Unity::Mathematics::float4>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::Unity::Mathematics::float4>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::Unity::Mathematics::float4>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::Unity::Mathematics::float4>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::Unity::Mathematics::float4>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::Unity::Mathematics::float4>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::Unity::Mathematics::float4>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::Unity::Mathematics::float4>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::System::Array1<::DotNet::Unity::Mathematics::float4>::Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float4* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::float4 Array1<::DotNet::Unity::Mathematics::float4>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::float4 result;
    Property_get_Item((*this).GetHandle().GetRaw(), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int32_t (*DotNet::System::Array1<::DotNet::Unity::Mathematics::float4>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::Unity::Mathematics::float4>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::Unity::Mathematics::float4>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::Unity::Mathematics::float4>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::Unity::Mathematics::float4>::SetItem)(void* thiz, std::int32_t, const ::DotNet::Unity::Mathematics::float4* value) = nullptr;


void Array1<::DotNet::Unity::Mathematics::float4>::Item(std::int32_t index, const ::DotNet::Unity::Mathematics::float4& value) {
  SetItem((*this).GetHandle().GetRaw(), index, &value);
}


Array1<::DotNet::Unity::Mathematics::float2x2>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::Unity::Mathematics::float2x2>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::Unity::Mathematics::float2x2>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::Unity::Mathematics::float2x2>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::Unity::Mathematics::float2x2>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::Unity::Mathematics::float2x2>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::Unity::Mathematics::float2x2>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::Unity::Mathematics::float2x2>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::System::Array1<::DotNet::Unity::Mathematics::float2x2>::Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float2x2* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::float2x2 Array1<::DotNet::Unity::Mathematics::float2x2>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::float2x2 result;
    Property_get_Item((*this).GetHandle().GetRaw(), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int32_t (*DotNet::System::Array1<::DotNet::Unity::Mathematics::float2x2>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::Unity::Mathematics::float2x2>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::Unity::Mathematics::float2x2>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::Unity::Mathematics::float2x2>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::Unity::Mathematics::float2x2>::SetItem)(void* thiz, std::int32_t, const ::DotNet::Unity::Mathematics::float2x2* value) = nullptr;


void Array1<::DotNet::Unity::Mathematics::float2x2>::Item(std::int32_t index, const ::DotNet::Unity::Mathematics::float2x2& value) {
  SetItem((*this).GetHandle().GetRaw(), index, &value);
}


Array1<::DotNet::Unity::Mathematics::float3x3>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::Unity::Mathematics::float3x3>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::Unity::Mathematics::float3x3>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::Unity::Mathematics::float3x3>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::Unity::Mathematics::float3x3>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::Unity::Mathematics::float3x3>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::Unity::Mathematics::float3x3>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::Unity::Mathematics::float3x3>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::System::Array1<::DotNet::Unity::Mathematics::float3x3>::Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float3x3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::float3x3 Array1<::DotNet::Unity::Mathematics::float3x3>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::float3x3 result;
    Property_get_Item((*this).GetHandle().GetRaw(), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int32_t (*DotNet::System::Array1<::DotNet::Unity::Mathematics::float3x3>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::Unity::Mathematics::float3x3>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::Unity::Mathematics::float3x3>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::Unity::Mathematics::float3x3>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::Unity::Mathematics::float3x3>::SetItem)(void* thiz, std::int32_t, const ::DotNet::Unity::Mathematics::float3x3* value) = nullptr;


void Array1<::DotNet::Unity::Mathematics::float3x3>::Item(std::int32_t index, const ::DotNet::Unity::Mathematics::float3x3& value) {
  SetItem((*this).GetHandle().GetRaw(), index, &value);
}


Array1<::DotNet::Unity::Mathematics::float4x4>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::Unity::Mathematics::float4x4>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::Unity::Mathematics::float4x4>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::Unity::Mathematics::float4x4>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::Unity::Mathematics::float4x4>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::Unity::Mathematics::float4x4>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::Unity::Mathematics::float4x4>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::Unity::Mathematics::float4x4>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::System::Array1<::DotNet::Unity::Mathematics::float4x4>::Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float4x4* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::float4x4 Array1<::DotNet::Unity::Mathematics::float4x4>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::float4x4 result;
    Property_get_Item((*this).GetHandle().GetRaw(), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int32_t (*DotNet::System::Array1<::DotNet::Unity::Mathematics::float4x4>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::Unity::Mathematics::float4x4>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::Unity::Mathematics::float4x4>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::Unity::Mathematics::float4x4>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::Unity::Mathematics::float4x4>::SetItem)(void* thiz, std::int32_t, const ::DotNet::Unity::Mathematics::float4x4* value) = nullptr;


void Array1<::DotNet::Unity::Mathematics::float4x4>::Item(std::int32_t index, const ::DotNet::Unity::Mathematics::float4x4& value) {
  SetItem((*this).GetHandle().GetRaw(), index, &value);
}


Array1<::DotNet::Unity::Mathematics::double3>::Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array1<::DotNet::Unity::Mathematics::double3>::Array1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array1<::DotNet::Unity::Mathematics::double3>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array1<::DotNet::Unity::Mathematics::double3>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::Unity::Mathematics::double3>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array1<::DotNet::Unity::Mathematics::double3>::GetHandle() {
    return this->_handle;
}


Array1<::DotNet::Unity::Mathematics::double3>::operator ::DotNet::System::Array() const {
    return ::DotNet::System::Array(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Array1<::DotNet::Unity::Mathematics::double3>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::System::Array1<::DotNet::Unity::Mathematics::double3>::Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::double3 Array1<::DotNet::Unity::Mathematics::double3>::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double3 result;
    Property_get_Item((*this).GetHandle().GetRaw(), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int32_t (*DotNet::System::Array1<::DotNet::Unity::Mathematics::double3>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array1<::DotNet::Unity::Mathematics::double3>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Array1<::DotNet::Unity::Mathematics::double3>::Construct_Size)(std::int32_t) = nullptr;


Array1<::DotNet::Unity::Mathematics::double3>::Array1(std::int32_t size)
  : _handle(Construct_Size(size))
{
}


void (*Array1<::DotNet::Unity::Mathematics::double3>::SetItem)(void* thiz, std::int32_t, const ::DotNet::Unity::Mathematics::double3* value) = nullptr;


void Array1<::DotNet::Unity::Mathematics::double3>::Item(std::int32_t index, const ::DotNet::Unity::Mathematics::double3& value) {
  SetItem((*this).GetHandle().GetRaw(), index, &value);
}


} // namespace DotNet::System


