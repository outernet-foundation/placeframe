#include <DotNet/UnityEditor/IMGUI/Controls/TreeViewItem.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/String.h>
#include <DotNet/System/Object.h>



namespace DotNet::UnityEditor::IMGUI::Controls {

TreeViewItem::TreeViewItem(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


TreeViewItem::TreeViewItem(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool TreeViewItem::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool TreeViewItem::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& TreeViewItem::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& TreeViewItem::GetHandle() {
    return this->_handle;
}


void* (*TreeViewItem::Construct_fAkE2H7EjTzReHiM2XHBPA)(::std::int32_t id, ::std::int32_t depth, void* displayName, void** reinteropException) = nullptr;


TreeViewItem::TreeViewItem(::std::int32_t id, ::std::int32_t depth, const ::DotNet::System::String& displayName)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_fAkE2H7EjTzReHiM2XHBPA(id, depth, displayName.GetHandle().GetRaw(), &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


TreeViewItem::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::UnityEditor::IMGUI::Controls::TreeViewItem::Property_get_id)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t TreeViewItem::id() const {
    void* reinteropException = nullptr;
    auto result = Property_get_id((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEditor::IMGUI::Controls::TreeViewItem::Property_set_id)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void TreeViewItem::id(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_id((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::UnityEditor::IMGUI::Controls


