#include <DotNet/UnityEditor/IMGUI/Controls/TreeView.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/UnityEditor/IMGUI/Controls/MultiColumnHeader.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/String.h>



namespace DotNet::UnityEditor::IMGUI::Controls {

TreeView::TreeView(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


TreeView::TreeView(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool TreeView::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool TreeView::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& TreeView::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& TreeView::GetHandle() {
    return this->_handle;
}


TreeView::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::UnityEditor::IMGUI::Controls::TreeView::Property_get_multiColumnHeader)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEditor::IMGUI::Controls::MultiColumnHeader TreeView::multiColumnHeader() const {
    void* reinteropException = nullptr;
    auto result = Property_get_multiColumnHeader((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEditor::IMGUI::Controls::MultiColumnHeader(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEditor::IMGUI::Controls::TreeView::Property_set_multiColumnHeader)(void* thiz, void* value, void** reinteropException) = nullptr;


void TreeView::multiColumnHeader(const ::DotNet::UnityEditor::IMGUI::Controls::MultiColumnHeader& value) const {
    void* reinteropException = nullptr;
    Property_set_multiColumnHeader((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEditor::IMGUI::Controls::TreeView::Property_get_searchString)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String TreeView::searchString() const {
    void* reinteropException = nullptr;
    auto result = Property_get_searchString((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEditor::IMGUI::Controls::TreeView::Property_set_searchString)(void* thiz, void* value, void** reinteropException) = nullptr;


void TreeView::searchString(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_searchString((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEditor::IMGUI::Controls::TreeView::CallReload_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void TreeView::Reload() const {
    void* reinteropException = nullptr;
    CallReload_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::UnityEditor::IMGUI::Controls


