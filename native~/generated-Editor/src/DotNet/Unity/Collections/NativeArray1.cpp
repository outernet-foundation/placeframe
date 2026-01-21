#include <cstdint>
#include <DotNet/Unity/Collections/NativeArray1.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/Unity/Collections/Allocator.h>
#include <DotNet/Unity/Collections/NativeArrayOptions.h>
#include <DotNet/UnityEngine/Vector3.h>
#include <DotNet/UnityEngine/Vector2.h>



namespace DotNet::Unity::Collections {

NativeArray1<::std::uint8_t>::NativeArray1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


NativeArray1<::std::uint8_t>::NativeArray1(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& NativeArray1<::std::uint8_t>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& NativeArray1<::std::uint8_t>::GetHandle() {
    return this->_handle;
}


void* (*NativeArray1<::std::uint8_t>::Construct_fyLz0cEPCtnsPNSt__omZwQ)(::std::int32_t length, ::std::uint32_t allocator, ::std::uint32_t options, void** reinteropException) = nullptr;


NativeArray1<::std::uint8_t>::NativeArray1(::std::int32_t length, ::DotNet::Unity::Collections::Allocator allocator, ::DotNet::Unity::Collections::NativeArrayOptions options)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_fyLz0cEPCtnsPNSt__omZwQ(length, ::std::uint32_t(allocator), ::std::uint32_t(options), &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


::std::int32_t (*DotNet::Unity::Collections::NativeArray1<::std::uint8_t>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t NativeArray1<::std::uint8_t>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::uint8_t (*DotNet::Unity::Collections::NativeArray1<::std::uint8_t>::Callop_Equality___ZFbUbDYmnqRGnwegIjKPw)(void* left, void* right, void** reinteropException) = nullptr;


bool NativeArray1<::std::uint8_t>::operator==(const ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>& rhs) const {
  return op_Equality(*this, rhs);
}


bool NativeArray1<::std::uint8_t>::op_Equality(const ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>& right) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality___ZFbUbDYmnqRGnwegIjKPw(left.GetHandle().GetRaw(), right.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::Unity::Collections::NativeArray1<::std::uint8_t>::Callop_Inequality___ZFbUbDYmnqRGnwegIjKPw)(void* left, void* right, void** reinteropException) = nullptr;


bool NativeArray1<::std::uint8_t>::operator!=(const ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>& rhs) const {
  return op_Inequality(*this, rhs);
}


bool NativeArray1<::std::uint8_t>::op_Inequality(const ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>& right) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality___ZFbUbDYmnqRGnwegIjKPw(left.GetHandle().GetRaw(), right.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


NativeArray1<::DotNet::UnityEngine::Vector3>::NativeArray1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


NativeArray1<::DotNet::UnityEngine::Vector3>::NativeArray1(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& NativeArray1<::DotNet::UnityEngine::Vector3>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& NativeArray1<::DotNet::UnityEngine::Vector3>::GetHandle() {
    return this->_handle;
}


void* (*NativeArray1<::DotNet::UnityEngine::Vector3>::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


NativeArray1<::DotNet::UnityEngine::Vector3>::NativeArray1()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


void* (*NativeArray1<::DotNet::UnityEngine::Vector3>::Construct_fyLz0cEPCtnsPNSt__omZwQ)(::std::int32_t length, ::std::uint32_t allocator, ::std::uint32_t options, void** reinteropException) = nullptr;


NativeArray1<::DotNet::UnityEngine::Vector3>::NativeArray1(::std::int32_t length, ::DotNet::Unity::Collections::Allocator allocator, ::DotNet::Unity::Collections::NativeArrayOptions options)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_fyLz0cEPCtnsPNSt__omZwQ(length, ::std::uint32_t(allocator), ::std::uint32_t(options), &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


::std::int32_t (*DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t NativeArray1<::DotNet::UnityEngine::Vector3>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::uint8_t (*DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>::Callop_Equality_vrdbfdWf_jNnpc3OykEL7A)(void* left, void* right, void** reinteropException) = nullptr;


bool NativeArray1<::DotNet::UnityEngine::Vector3>::operator==(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>& rhs) const {
  return op_Equality(*this, rhs);
}


bool NativeArray1<::DotNet::UnityEngine::Vector3>::op_Equality(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>& left, const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>& right) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_vrdbfdWf_jNnpc3OykEL7A(left.GetHandle().GetRaw(), right.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>::Callop_Inequality_vrdbfdWf_jNnpc3OykEL7A)(void* left, void* right, void** reinteropException) = nullptr;


bool NativeArray1<::DotNet::UnityEngine::Vector3>::operator!=(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>& rhs) const {
  return op_Inequality(*this, rhs);
}


bool NativeArray1<::DotNet::UnityEngine::Vector3>::op_Inequality(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>& left, const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>& right) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_vrdbfdWf_jNnpc3OykEL7A(left.GetHandle().GetRaw(), right.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void NativeArray1<::DotNet::UnityEngine::Vector3>::Dispose() const {
    void* reinteropException = nullptr;
    CallDispose_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


NativeArray1<::DotNet::UnityEngine::Vector2>::NativeArray1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


NativeArray1<::DotNet::UnityEngine::Vector2>::NativeArray1(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& NativeArray1<::DotNet::UnityEngine::Vector2>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& NativeArray1<::DotNet::UnityEngine::Vector2>::GetHandle() {
    return this->_handle;
}


void* (*NativeArray1<::DotNet::UnityEngine::Vector2>::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


NativeArray1<::DotNet::UnityEngine::Vector2>::NativeArray1()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


void* (*NativeArray1<::DotNet::UnityEngine::Vector2>::Construct_fyLz0cEPCtnsPNSt__omZwQ)(::std::int32_t length, ::std::uint32_t allocator, ::std::uint32_t options, void** reinteropException) = nullptr;


NativeArray1<::DotNet::UnityEngine::Vector2>::NativeArray1(::std::int32_t length, ::DotNet::Unity::Collections::Allocator allocator, ::DotNet::Unity::Collections::NativeArrayOptions options)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_fyLz0cEPCtnsPNSt__omZwQ(length, ::std::uint32_t(allocator), ::std::uint32_t(options), &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


::std::int32_t (*DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t NativeArray1<::DotNet::UnityEngine::Vector2>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::uint8_t (*DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>::Callop_Equality_upxAhiBTuli9tU8WNSSzEg)(void* left, void* right, void** reinteropException) = nullptr;


bool NativeArray1<::DotNet::UnityEngine::Vector2>::operator==(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>& rhs) const {
  return op_Equality(*this, rhs);
}


bool NativeArray1<::DotNet::UnityEngine::Vector2>::op_Equality(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>& left, const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>& right) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_upxAhiBTuli9tU8WNSSzEg(left.GetHandle().GetRaw(), right.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>::Callop_Inequality_upxAhiBTuli9tU8WNSSzEg)(void* left, void* right, void** reinteropException) = nullptr;


bool NativeArray1<::DotNet::UnityEngine::Vector2>::operator!=(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>& rhs) const {
  return op_Inequality(*this, rhs);
}


bool NativeArray1<::DotNet::UnityEngine::Vector2>::op_Inequality(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>& left, const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>& right) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_upxAhiBTuli9tU8WNSSzEg(left.GetHandle().GetRaw(), right.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void NativeArray1<::DotNet::UnityEngine::Vector2>::Dispose() const {
    void* reinteropException = nullptr;
    CallDispose_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


NativeArray1<::std::int32_t>::NativeArray1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


NativeArray1<::std::int32_t>::NativeArray1(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& NativeArray1<::std::int32_t>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& NativeArray1<::std::int32_t>::GetHandle() {
    return this->_handle;
}


void* (*NativeArray1<::std::int32_t>::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


NativeArray1<::std::int32_t>::NativeArray1()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


void* (*NativeArray1<::std::int32_t>::Construct_fyLz0cEPCtnsPNSt__omZwQ)(::std::int32_t length, ::std::uint32_t allocator, ::std::uint32_t options, void** reinteropException) = nullptr;


NativeArray1<::std::int32_t>::NativeArray1(::std::int32_t length, ::DotNet::Unity::Collections::Allocator allocator, ::DotNet::Unity::Collections::NativeArrayOptions options)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_fyLz0cEPCtnsPNSt__omZwQ(length, ::std::uint32_t(allocator), ::std::uint32_t(options), &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


::std::uint8_t (*DotNet::Unity::Collections::NativeArray1<::std::int32_t>::Callop_Equality_udAsXu_l5uh9odAsOsJXHQ)(void* left, void* right, void** reinteropException) = nullptr;


bool NativeArray1<::std::int32_t>::operator==(const ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>& rhs) const {
  return op_Equality(*this, rhs);
}


bool NativeArray1<::std::int32_t>::op_Equality(const ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>& right) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_udAsXu_l5uh9odAsOsJXHQ(left.GetHandle().GetRaw(), right.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::Unity::Collections::NativeArray1<::std::int32_t>::Callop_Inequality_udAsXu_l5uh9odAsOsJXHQ)(void* left, void* right, void** reinteropException) = nullptr;


bool NativeArray1<::std::int32_t>::operator!=(const ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>& rhs) const {
  return op_Inequality(*this, rhs);
}


bool NativeArray1<::std::int32_t>::op_Inequality(const ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>& right) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_udAsXu_l5uh9odAsOsJXHQ(left.GetHandle().GetRaw(), right.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::Unity::Collections::NativeArray1<::std::int32_t>::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void NativeArray1<::std::int32_t>::Dispose() const {
    void* reinteropException = nullptr;
    CallDispose_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


NativeArray1<::std::uint16_t>::NativeArray1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


NativeArray1<::std::uint16_t>::NativeArray1(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& NativeArray1<::std::uint16_t>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& NativeArray1<::std::uint16_t>::GetHandle() {
    return this->_handle;
}


::std::int32_t (*DotNet::Unity::Collections::NativeArray1<::std::uint16_t>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t NativeArray1<::std::uint16_t>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::uint8_t (*DotNet::Unity::Collections::NativeArray1<::std::uint16_t>::Callop_Equality_V583jKrqBJAPH29Lt9agWA)(void* left, void* right, void** reinteropException) = nullptr;


bool NativeArray1<::std::uint16_t>::operator==(const ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>& rhs) const {
  return op_Equality(*this, rhs);
}


bool NativeArray1<::std::uint16_t>::op_Equality(const ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>& right) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_V583jKrqBJAPH29Lt9agWA(left.GetHandle().GetRaw(), right.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::Unity::Collections::NativeArray1<::std::uint16_t>::Callop_Inequality_V583jKrqBJAPH29Lt9agWA)(void* left, void* right, void** reinteropException) = nullptr;


bool NativeArray1<::std::uint16_t>::operator!=(const ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>& rhs) const {
  return op_Inequality(*this, rhs);
}


bool NativeArray1<::std::uint16_t>::op_Inequality(const ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>& right) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_V583jKrqBJAPH29Lt9agWA(left.GetHandle().GetRaw(), right.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


NativeArray1<::std::uint32_t>::NativeArray1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


NativeArray1<::std::uint32_t>::NativeArray1(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& NativeArray1<::std::uint32_t>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& NativeArray1<::std::uint32_t>::GetHandle() {
    return this->_handle;
}


::std::int32_t (*DotNet::Unity::Collections::NativeArray1<::std::uint32_t>::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t NativeArray1<::std::uint32_t>::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::uint8_t (*DotNet::Unity::Collections::NativeArray1<::std::uint32_t>::Callop_Equality_Mjak7jxj5GQBeCOOhOuHAw)(void* left, void* right, void** reinteropException) = nullptr;


bool NativeArray1<::std::uint32_t>::operator==(const ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>& rhs) const {
  return op_Equality(*this, rhs);
}


bool NativeArray1<::std::uint32_t>::op_Equality(const ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>& right) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_Mjak7jxj5GQBeCOOhOuHAw(left.GetHandle().GetRaw(), right.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::Unity::Collections::NativeArray1<::std::uint32_t>::Callop_Inequality_Mjak7jxj5GQBeCOOhOuHAw)(void* left, void* right, void** reinteropException) = nullptr;


bool NativeArray1<::std::uint32_t>::operator!=(const ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>& rhs) const {
  return op_Inequality(*this, rhs);
}


bool NativeArray1<::std::uint32_t>::op_Inequality(const ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>& right) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_Mjak7jxj5GQBeCOOhOuHAw(left.GetHandle().GetRaw(), right.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


} // namespace DotNet::Unity::Collections


