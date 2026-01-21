#include <DotNet/CesiumForUnity/QuickAddItem.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/QuickAddItemType.h>
#include <DotNet/System/String.h>
#include <DotNet/System/Object.h>



namespace DotNet::CesiumForUnity {

QuickAddItem::QuickAddItem(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


QuickAddItem::QuickAddItem(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool QuickAddItem::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool QuickAddItem::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& QuickAddItem::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& QuickAddItem::GetHandle() {
    return this->_handle;
}


void* (*QuickAddItem::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


QuickAddItem::QuickAddItem()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


void* (*QuickAddItem::Construct_MigqS33KRbgyAt6uiJjTGw)(::std::uint32_t type, void* name, void* tooltip, void* tilesetName, ::std::int64_t tilesetId, void* overlayName, ::std::int64_t overlayId, void** reinteropException) = nullptr;


QuickAddItem::QuickAddItem(::DotNet::CesiumForUnity::QuickAddItemType type, const ::DotNet::System::String& name, const ::DotNet::System::String& tooltip, const ::DotNet::System::String& tilesetName, ::std::int64_t tilesetId, const ::DotNet::System::String& overlayName, ::std::int64_t overlayId)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_MigqS33KRbgyAt6uiJjTGw(::std::uint32_t(type), name.GetHandle().GetRaw(), tooltip.GetHandle().GetRaw(), tilesetName.GetHandle().GetRaw(), tilesetId, overlayName.GetHandle().GetRaw(), overlayId, &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


QuickAddItem::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint32_t (*DotNet::CesiumForUnity::QuickAddItem::Field_get_type)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::QuickAddItem::Field_set_type)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::QuickAddItemType QuickAddItem::type() const {
    void* reinteropException = nullptr;
    auto result = Field_get_type((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::CesiumForUnity::QuickAddItemType(result);
}


void QuickAddItem::type(::DotNet::CesiumForUnity::QuickAddItemType value) const {
    void* reinteropException = nullptr;
    Field_set_type((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void* (*DotNet::CesiumForUnity::QuickAddItem::Field_get_name)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::QuickAddItem::Field_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


::DotNet::System::String QuickAddItem::name() const {
    void* reinteropException = nullptr;
    auto result = Field_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void QuickAddItem::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Field_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void* (*DotNet::CesiumForUnity::QuickAddItem::Field_get_tooltip)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::QuickAddItem::Field_set_tooltip)(void* thiz, void* value, void** reinteropException) = nullptr;


::DotNet::System::String QuickAddItem::tooltip() const {
    void* reinteropException = nullptr;
    auto result = Field_get_tooltip((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void QuickAddItem::tooltip(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Field_set_tooltip((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void* (*DotNet::CesiumForUnity::QuickAddItem::Field_get_tilesetName)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::QuickAddItem::Field_set_tilesetName)(void* thiz, void* value, void** reinteropException) = nullptr;


::DotNet::System::String QuickAddItem::tilesetName() const {
    void* reinteropException = nullptr;
    auto result = Field_get_tilesetName((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void QuickAddItem::tilesetName(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Field_set_tilesetName((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


::std::int64_t (*DotNet::CesiumForUnity::QuickAddItem::Field_get_tilesetId)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::QuickAddItem::Field_set_tilesetId)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


::std::int64_t QuickAddItem::tilesetId() const {
    void* reinteropException = nullptr;
    auto result = Field_get_tilesetId((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return result;
}


void QuickAddItem::tilesetId(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Field_set_tilesetId((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void* (*DotNet::CesiumForUnity::QuickAddItem::Field_get_overlayName)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::QuickAddItem::Field_set_overlayName)(void* thiz, void* value, void** reinteropException) = nullptr;


::DotNet::System::String QuickAddItem::overlayName() const {
    void* reinteropException = nullptr;
    auto result = Field_get_overlayName((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void QuickAddItem::overlayName(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Field_set_overlayName((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


::std::int64_t (*DotNet::CesiumForUnity::QuickAddItem::Field_get_overlayId)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::QuickAddItem::Field_set_overlayId)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


::std::int64_t QuickAddItem::overlayId() const {
    void* reinteropException = nullptr;
    auto result = Field_get_overlayId((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return result;
}


void QuickAddItem::overlayId(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Field_set_overlayId((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


} // namespace DotNet::CesiumForUnity


